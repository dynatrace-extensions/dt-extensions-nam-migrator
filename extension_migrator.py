import json
import os
import re
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

import requests
import typer
from dynatrace import Dynatrace
from typing_extensions import Annotated

from converter import convert_endpoint_to_monitor
from converter_config import ConverterConfig
from extension_type import ExtensionType

NAM_MONITORS_API = "/api/v2/synthetic/monitors"
VALID_FREQUENCY_LIST = [1, 2, 5, 10, 15, 30, 60]

app = typer.Typer()


def valid_frequency(value: str) -> Optional[str]:
    if value is None or (value.isdigit() and int(value) in VALID_FREQUENCY_LIST):
        return value
    else:
        raise typer.BadParameter(f"Invalid frequency, valid numbers = {VALID_FREQUENCY_LIST}")


@app.command()
def post(
        dt_url: Annotated[str, typer.Option(envvar="DT_URL")],
        dt_token: Annotated[str, typer.Option(envvar="DT_TOKEN")],
        work_dir: Annotated[Path, typer.Argument(help="Directory to load monitor configuration and write monitor ids")]
):
    config_files = [f for f in os.listdir(work_dir) if os.path.isfile(os.path.join(work_dir, f)) and f.endswith("monitor.json")]
    added_monitor_ids = []
    for file in config_files:

        with open(os.path.join(work_dir, file), "r") as config_handle:
            monitor_json = json.load(config_handle)
        request = requests.post(f"{dt_url}{NAM_MONITORS_API}",
                                headers={"Authorization": f"Api-Token {dt_token}"},
                                json=monitor_json)
        if request.status_code == 200:
            print(f"Uploaded the NAM monitor: {file} successfully! Response: {request.text}.")
            added_monitor_ids.append(json.loads(request.text)["entityId"])
        else:
            print(f"Failed to upload the NAM monitor! Status code: {request.status_code}, response: {request.text}")

    if added_monitor_ids:
        added_monitor_ids_output = os.path.join(work_dir, "nam_monitor_ids.json")
        with open(added_monitor_ids_output, "w") as ids_handle:
            json.dump(added_monitor_ids, ids_handle, indent=4)
        print(f"Saved ids of the created monitors to '{added_monitor_ids_output}'.")


@app.command()
def get(
        dt_url: Annotated[str, typer.Option(envvar="DT_URL")],
        dt_token: Annotated[str, typer.Option(envvar="DT_TOKEN")],
        location: Annotated[List[str], typer.Argument(help="Synthetic location id")],
        work_dir: Annotated[Path, typer.Argument(help="Directory to write monitor configuration")],
        extension_type: Annotated[ExtensionType, typer.Option(help="Extension name to migrate to NAM monitors")] = None,
        enabled: Annotated[bool, typer.Option(help="Enable imported monitors")] = ConverterConfig.enable_monitors,
        frequency_min: Annotated[str, typer.Option(
            help=f"Time between monitor executions in minutes, valid numbers = {VALID_FREQUENCY_LIST}",
            callback=valid_frequency)] = ConverterConfig.frequency_min,
):
    dt = Dynatrace(dt_url, dt_token)
    converter_config = ConverterConfig(
        frequency_min=frequency_min,
        enable_monitors=enabled,
    )

    if not os.path.isdir(work_dir):
        try:
            print(f"Directory '{work_dir}' does not exist, creating...")
            os.mkdir(work_dir)
        except IOError as error:
            raise Exception(f"Unable to create directory '{work_dir}', {error}. Aborting.")

    if extension_type is None:
        extension_types_to_convert = [ExtensionType.dns, ExtensionType.ping, ExtensionType.port]
    else:
        extension_types_to_convert = [extension_type]

    for extension_type in extension_types_to_convert:
        extension_endpoints = list(dt.extensions.list_instances(extension_id=extension_type.get_extension_id()))
        for endpoint in extension_endpoints:
            endpoint_config = endpoint.get_full_configuration(extension_type.get_extension_id()).json()
            if endpoint_config["properties"]["proxy_address"]:
                print(f"Proxy servers are not supported for NAM monitors. Aborting migration of the endpoint '{endpoint.name}'.")
                continue
            if extension_type.get_nam_monitor_type() == "TCP" and endpoint_config["properties"]["test_protocol"] == "UDP":
                print(f"UDP protocol monitors are not supported in NAM. Aborting migration of the endpoint '{endpoint.name}'.")
                continue
            monitor_definition = convert_endpoint_to_monitor(extension_type.get_nam_monitor_type(),
                                                             endpoint_config,
                                                             location,
                                                             converter_config)
            monitor_filename = f"{work_dir}/{uuid4().hex}-{re.sub('[^0-9a-zA-Z_-]',
                                                                  '',
                                                                  endpoint.name.replace(' ', '')
                                                                  )}-{extension_type.name}-monitor.json"
            try:
                with open(monitor_filename, "w") as file_handle:
                    json.dump(monitor_definition, file_handle, indent=4)
                print(f"Saved monitor config to the file: '{monitor_filename}'.")
            except IOError as error:
                print(f"Unable to save JSON to the file: '{monitor_filename}', {error}.")


if __name__ == "__main__":
    app()

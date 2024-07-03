import datetime
import json
from typing import List

from converter_config import ConverterConfig


def convert_endpoint_to_monitor(
    monitor_type: str,
    endpoint_config: dict,
    locations: List[str],
    converter_config: ConverterConfig
) -> dict:
    tag_date = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with open("nam_monitor_template.json", "r") as template_handle:
        monitor_configuration = json.load(template_handle)

    monitor_name = endpoint_config["properties"]["test_name"] if endpoint_config["properties"]["test_name"] else endpoint_config["endpointName"]
    properties = {}
    constraints = []

    target = ""
    if monitor_type == "DNS":
        target = endpoint_config["properties"]["host"]
        properties["DNS_RECORD_TYPES"] = "A"
        if endpoint_config["properties"]["dns_server"]:
            properties["DNS_SERVER"] = endpoint_config["properties"]["dns_server"]
        constraints.append(
            {
                "type": "DNS_STATUS_CODE",
                "properties": {
                    "operator": "=",
                    "status": "NOERROR"
                }
            }
        )
    elif monitor_type == "ICMP":
        target = endpoint_config["properties"]["test_target"]
        properties["ICMP_NUMBER_OF_PACKETS"] = converter_config.icmp_number_of_packets
        properties["ICMP_PACKET_SIZE"] = converter_config.icmp_packet_size
        properties["ICMP_TIMEOUT_FOR_REPLY"] = f"PT{converter_config.icmp_timeout_for_reply}S"
        constraints.append(
            {
                "type": "ICMP_SUCCESS_RATE_PERCENT",
                "properties": {
                    "operator": ">=",
                    "value": converter_config.icmp_success_rate_percent
                }
            }
        )
    elif monitor_type == "TCP":
        if endpoint_config["properties"]["test_timeout"] == "0":
            properties["EXECUTION_TIMEOUT"] = f"PT{converter_config.tcp_default_execution_timeout}S"
        target = endpoint_config["properties"]["test_target_ip"]
        properties["TCP_PORT_RANGES"] = endpoint_config["properties"]["test_target_ports"]

    if converter_config.frequency_min:
        frequency = converter_config.frequency_min
    elif endpoint_config["properties"]["frequency"]:
        frequency = endpoint_config["properties"]["frequency"]
    else:
        frequency = converter_config.default_frequency_min

    monitor_configuration["enabled"] = converter_config.enable_monitors
    monitor_configuration["frequencyMin"] = frequency
    monitor_configuration["locations"] = locations
    monitor_configuration["name"] = monitor_name
    monitor_configuration["steps"][0]["name"] = monitor_name
    monitor_configuration["steps"][0]["properties"] = properties
    monitor_configuration["steps"][0]["requestConfigurations"][0]["constraints"] = constraints
    monitor_configuration["steps"][0]["requestType"] = monitor_type
    monitor_configuration["steps"][0]["targetList"] = [target]
    monitor_configuration["tags"].append({"key": "generation-date", "value": tag_date})
    return monitor_configuration

from enum import Enum


class ExtensionType(str, Enum):
    dns = "dns"
    ping = "ping"
    port = "port"

    def get_nam_monitor_type(self):
        if self == ExtensionType.dns:
            return "DNS"
        elif self == ExtensionType.ping:
            return "ICMP"
        elif self == ExtensionType.port:
            return "TCP"

    def get_extension_id(self):
        if self == ExtensionType.dns:
            return "custom.remote.python.thirdparty_dns"
        elif self == ExtensionType.ping:
            return "custom.remote.python.thirdparty_ping"
        elif self == ExtensionType.port:
            return "custom.remote.python.thirdparty_port"

class ConverterConfig:
    # modifiable by CLI parameters
    enable_monitors = False
    frequency_min = None

    # default configuration
    default_frequency_min = "1"
    dns_record_type = "A"
    tcp_default_execution_timeout = "2"
    icmp_number_of_packets = "1"
    icmp_packet_size = "32"
    icmp_success_rate_percent = "80"
    icmp_timeout_for_reply = "1"

    def __init__(self, **kwargs):
        self.enable_monitors = kwargs.get("enable_monitors")
        self.frequency_min = kwargs.get("frequency_min")

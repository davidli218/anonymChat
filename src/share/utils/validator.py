import re


def valid_ip_port(ip_port: str) -> bool:
    compile_ip = re.compile(
        r"^(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|[1-9])\."
        r"(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\."
        r"(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d)\."
        r"(1\d{2}|2[0-4]\d|25[0-5]|[1-9]\d|\d):"
        r"([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$")

    return True if compile_ip.match(ip_port) else False

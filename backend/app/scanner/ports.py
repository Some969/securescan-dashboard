import os
import re
import shutil
import subprocess
from typing import Dict, List

from app.utils import hostname_from_url

NMAP_TIMEOUT = int(os.getenv("SECURESCAN_NMAP_TIMEOUT", "60"))
ALLOWED_WEB_PORTS = {80, 443}
RISKIER_PORTS = {21, 22, 23, 25, 110, 143, 445, 3306, 3389, 5432, 6379, 8080}


def find_nmap_executable() -> str | None:
    detected = shutil.which("nmap")
    if detected:
        return detected

    common_windows_paths = [
        r"C:\Program Files (x86)\Nmap\nmap.exe",
        r"C:\Program Files\Nmap\nmap.exe",
    ]

    for path in common_windows_paths:
        if os.path.exists(path):
            return path

    return None


def check_open_ports(target_url: str) -> Dict:
    hostname = hostname_from_url(target_url)
    findings: List[dict] = []

    nmap_path = find_nmap_executable()
    if nmap_path is None:
        return {
            "ok": False,
            "nmap_available": False,
            "command": "nmap -T3 --top-ports 20 <hostname>",
            "open_ports": [],
            "error": "Nmap is not installed or is not available in PATH.",
            "findings": findings,
        }

    command = [nmap_path, "-T3", "--top-ports", "20", hostname]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=NMAP_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "nmap_available": True,
            "command": " ".join(command),
            "open_ports": [],
            "error": "Nmap scan timed out.",
            "findings": findings,
        }
    except OSError as exc:
        return {
            "ok": False,
            "nmap_available": True,
            "command": " ".join(command),
            "open_ports": [],
            "error": f"Could not run Nmap: {exc}",
            "findings": findings,
        }

    open_ports = _parse_nmap_output(completed.stdout)

    for item in open_ports:
        port = item["port"]
        if port not in ALLOWED_WEB_PORTS:
            severity = "medium" if port in RISKIER_PORTS else "low"
            findings.append({
                "title": f"Open non-web port detected: {port}/{item['protocol']}",
                "description": f"Nmap reported port {port}/{item['protocol']} as open for service '{item['service']}'. This is not automatically a vulnerability, but it should be reviewed.",
                "severity": severity,
                "affected_component": "Network Exposure",
                "recommendation": "Confirm that this port is required. Restrict it by firewall or access control if it should not be public.",
            })

    return {
        "ok": completed.returncode == 0,
        "nmap_available": True,
        "command": " ".join(command),
        "open_ports": open_ports,
        "raw_return_code": completed.returncode,
        "error": completed.stderr.strip() or None,
        "findings": findings,
    }


def _parse_nmap_output(output: str) -> List[dict]:
    ports: List[dict] = []
    pattern = re.compile(r"^(\d+)/(\w+)\s+(\w+)\s+(.+)$")

    for line in output.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        port, protocol, state, service = match.groups()
        if state.lower() == "open":
            ports.append({
                "port": int(port),
                "protocol": protocol,
                "state": state,
                "service": service.strip(),
            })
    return ports

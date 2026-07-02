import re
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests

from app.utils import REQUEST_TIMEOUT, safe_get

LIBRARY_PATTERNS = {
    "jQuery": re.compile(r"jquery(?:-|/|@)?(?P<version>\d+\.\d+(?:\.\d+)?)?", re.IGNORECASE),
    "Bootstrap": re.compile(r"bootstrap(?:\.|-|/|@)?(?P<version>\d+\.\d+(?:\.\d+)?)?", re.IGNORECASE),
    "React": re.compile(r"react(?:\.|-|/|@)?(?P<version>\d+\.\d+(?:\.\d+)?)?", re.IGNORECASE),
    "Angular": re.compile(r"angular(?:\.|-|/|@)?(?P<version>\d+\.\d+(?:\.\d+)?)?", re.IGNORECASE),
    "Vue": re.compile(r"vue(?:\.|-|/|@)?(?P<version>\d+\.\d+(?:\.\d+)?)?", re.IGNORECASE),
}

SCRIPT_SRC_PATTERN = re.compile(r"<script[^>]+src=[\"'](?P<src>[^\"']+)[\"']", re.IGNORECASE)


def check_frontend_libraries(target_url: str) -> Dict:
    findings: List[dict] = []
    libraries = []

    try:
        response = safe_get(target_url, timeout=REQUEST_TIMEOUT)
        html = response.text[:750_000]  # keep parsing lightweight
    except requests.RequestException as exc:
        return {
            "ok": False,
            "error": f"Could not fetch HTML for library hints: {exc}",
            "libraries": libraries,
            "findings": findings,
        }

    seen = set()
    script_sources = SCRIPT_SRC_PATTERN.findall(html)

    for src in script_sources:
        absolute_src = urljoin(target_url, src)
        for library_name, pattern in LIBRARY_PATTERNS.items():
            match = pattern.search(src)
            if not match:
                continue

            version = _safe_group(match, "version")
            key = (library_name, version, absolute_src)
            if key in seen:
                continue
            seen.add(key)

            status = "needs manual review"
            description = f"Detected a possible {library_name} script reference."
            if version:
                status = "informational"
                description = f"Detected {library_name} version {version} from a script URL. This does not prove a vulnerability by itself."

            libraries.append({
                "name": library_name,
                "version": version,
                "source": absolute_src,
                "confidence": "medium" if version else "low",
                "status": status,
            })
            findings.append({
                "title": f"Frontend library hint: {library_name}",
                "description": description,
                "severity": "info",
                "affected_component": "Frontend Dependencies",
                "recommendation": "Manually confirm the dependency version and keep frontend libraries updated through your package manager or CDN.",
            })

    return {
        "ok": True,
        "libraries": libraries,
        "findings": findings,
    }


def _safe_group(match: re.Match, name: str) -> Optional[str]:
    try:
        return match.group(name)
    except IndexError:
        return None

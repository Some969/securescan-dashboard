import json
from datetime import datetime, timezone
from typing import Callable, Dict, List

from sqlalchemy.orm import Session

from app.models import ScanResult
from app.scanner.cookies import check_cookies
from app.scanner.headers import check_security_headers
from app.scanner.libraries import check_frontend_libraries
from app.scanner.ports import check_open_ports
from app.scanner.redirects import check_https_redirect
from app.scanner.recommendations import unique_recommendations
from app.scanner.scoring import score_findings, summarize_findings
from app.scanner.server_leakage import check_server_leakage
from app.scanner.ssl_check import check_ssl
from app.utils import normalize_url

ScannerFunction = Callable[[str], Dict]

SCANNERS: Dict[str, ScannerFunction] = {
    "ssl": check_ssl,
    "headers": check_security_headers,
    "cookies": check_cookies,
    "redirect": check_https_redirect,
    "server_leakage": check_server_leakage,
    "ports": check_open_ports,
    "libraries": check_frontend_libraries,
}


def run_scan(db: Session, raw_target_url: str) -> Dict:
    target_url = normalize_url(raw_target_url)
    checks: Dict[str, Dict] = {}
    findings: List[dict] = []

    for check_name, scanner in SCANNERS.items():
        result = _safe_run_scanner(scanner, target_url)
        checks[check_name] = result
        findings.extend(result.get("findings", []))

    scoring = score_findings(findings)
    summary = summarize_findings(findings)
    recommendations = unique_recommendations(findings)

    report_without_id = {
        "id": None,
        "target_url": target_url,
        "scan_date": datetime.now(timezone.utc).isoformat(),
        "risk_score": scoring["risk_score"],
        "grade": scoring["grade"],
        "summary": summary,
        "checks": checks,
        "findings": findings,
        "recommendations": recommendations,
    }

    record = ScanResult(
        target_url=target_url,
        risk_score=scoring["risk_score"],
        grade=scoring["grade"],
        total_findings=summary["total_findings"],
        report_json=json.dumps(report_without_id, default=str),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    report = dict(report_without_id)
    report["id"] = record.id
    report["scan_date"] = record.scan_date

    # Store a final copy with the database ID for later retrieval.
    record.report_json = json.dumps(_json_ready(report), default=str)
    db.commit()

    return report


def get_scan_report(db: Session, scan_id: int) -> Dict | None:
    record = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not record:
        return None
    return json.loads(record.report_json)


def delete_scan(db: Session, scan_id: int) -> bool:
    record = db.query(ScanResult).filter(ScanResult.id == scan_id).first()
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def _safe_run_scanner(scanner: ScannerFunction, target_url: str) -> Dict:
    try:
        return scanner(target_url)
    except Exception as exc:  # keeps one broken module from crashing the full scan
        return {
            "ok": False,
            "error": f"Scanner module failed safely: {exc}",
            "findings": [],
        }


def _json_ready(value):
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return value

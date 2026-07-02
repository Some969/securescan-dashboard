from typing import Dict, List

SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
    "info": 0,
}


def score_findings(findings: List[dict]) -> Dict:
    score = 100

    for finding in findings:
        score -= SEVERITY_WEIGHTS.get(finding.get("severity", "info"), 0)

    cookie_penalty = 0
    for finding in findings:
        title = str(finding.get("title", "")).lower()
        if "missing secure" in title:
            cookie_penalty += 3
        elif "missing httponly" in title:
            cookie_penalty += 3
        elif "missing samesite" in title:
            cookie_penalty += 2

    cookie_penalty = min(10, cookie_penalty)
    score -= cookie_penalty
    score = max(0, min(100, score))
    return {"risk_score": score, "grade": grade_for_score(score)}


def grade_for_score(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def summarize_findings(findings: List[dict]) -> Dict:
    summary = {
        "total_findings": len(findings),
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
    }
    for finding in findings:
        severity = finding.get("severity", "info")
        if severity in summary:
            summary[severity] += 1
    return summary

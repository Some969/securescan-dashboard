import os
import re
import tempfile
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.models import ScanResult
from app.schemas import DeleteResponse, HealthResponse, ScanHistoryItem, ScanReport, ScanRequest
from app.services.pdf_service import PDFGenerationError, generate_scan_pdf
from app.services.scan_service import delete_scan, get_scan_report, run_scan

app = FastAPI(
    title="SecureScan Dashboard API",
    description="A defensive website security scanning API for owned or authorized targets.",
    version="1.0.0",
)

allowed_origins = os.getenv(
    "SECURESCAN_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok", "service": "securescan-api", "version": "1.0.0"}


@app.post("/scan", response_model=ScanReport, status_code=status.HTTP_201_CREATED)
def create_scan(payload: ScanRequest, db: Session = Depends(get_db)):
    return run_scan(db, payload.target_url)


@app.get("/scans", response_model=List[ScanHistoryItem])
def list_scans(db: Session = Depends(get_db)):
    return (
        db.query(ScanResult)
        .order_by(ScanResult.scan_date.desc())
        .all()
    )


@app.get("/scans/{scan_id}", response_model=ScanReport)
def read_scan(scan_id: int, db: Session = Depends(get_db)):
    report = get_scan_report(db, scan_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return report


@app.delete("/scans/{scan_id}", response_model=DeleteResponse)
def remove_scan(scan_id: int, db: Session = Depends(get_db)):
    deleted = delete_scan(db, scan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scan not found.")
    return {"message": "Scan deleted successfully."}


@app.get("/scans/{scan_id}/pdf")
def download_scan_pdf(scan_id: int, db: Session = Depends(get_db)):
    report = get_scan_report(db, scan_id)
    if not report:
        raise HTTPException(status_code=404, detail="Scan not found.")

    try:
        pdf_bytes = generate_scan_pdf(report)
        safe_name = _safe_filename(report.get("target_url", "scan"))
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(pdf_bytes.getvalue())
            temp_path = temp_file.name

        filename = f"{safe_name}_{scan_id}.pdf"
        return FileResponse(
            temp_path,
            media_type="application/pdf",
            filename=filename,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    except PDFGenerationError as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "pdf_generation_failed", "message": str(exc), "status": "failed"},
        )
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"error": "pdf_generation_error", "message": f"Unexpected PDF error: {exc}", "status": "failed"},
        )


def _safe_filename(target_url: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", target_url).strip("._-") or "scan"
    return cleaned[:80]

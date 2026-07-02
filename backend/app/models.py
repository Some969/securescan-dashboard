from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    target_url = Column(String(500), nullable=False, index=True)
    scan_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    risk_score = Column(Integer, nullable=False)
    grade = Column(String(2), nullable=False)
    total_findings = Column(Integer, nullable=False, default=0)
    report_json = Column(Text, nullable=False)

"""
Logging and audit trail for the data pipeline
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger  # Optional: for JSON logging

from .config import config


class StructuredLogFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "run_id": getattr(record, "run_id", None),
            "stage": getattr(record, "stage", None),
        }
        
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(run_id: Optional[str] = None) -> logging.Logger:
    """Setup logging with both console and file handlers"""
    
    logger = logging.getLogger("parentmap_pipeline")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Clear existing handlers
    logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (JSON)
    log_file = config.logs_dir / f"pipeline_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(StructuredLogFormatter())
    logger.addHandler(file_handler)
    
    # Add run_id to logger adapter
    if run_id:
        logger = logging.LoggerAdapter(logger, {"run_id": run_id})
    
    return logger


class AuditLogger:
    """Audit trail for all data changes"""
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.audit_file = config.logs_dir / f"audit_{run_id}.jsonl"
        self.entries: list = []
    
    def log(
        self,
        action: str,
        place_id: str,
        details: Dict[str, Any],
        evidence_urls: Optional[list] = None
    ):
        """Log an audit entry"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "run_id": self.run_id,
            "action": action,
            "place_id": place_id,
            "details": details,
            "evidence_urls": evidence_urls or [],
        }
        self.entries.append(entry)
        
        # Write to file immediately
        with open(self.audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False, default=str) + '\n')
    
    def log_extraction(
        self,
        place_id: str,
        source_url: str,
        extracted_fields: Dict[str, Any]
    ):
        """Log extraction of a new place"""
        self.log(
            action="EXTRACT",
            place_id=place_id,
            details={
                "source_url": source_url,
                "extracted_fields": list(extracted_fields.keys()),
            },
            evidence_urls=[source_url]
        )
    
    def log_validation(
        self,
        place_id: str,
        validation_stage: str,
        confidence: int,
        evidence_urls: list
    ):
        """Log validation check"""
        self.log(
            action="VALIDATE",
            place_id=place_id,
            details={
                "stage": validation_stage,
                "confidence": confidence,
            },
            evidence_urls=evidence_urls
        )
    
    def log_status_change(
        self,
        place_id: str,
        old_status: str,
        new_status: str,
        reason: str,
        evidence_urls: list
    ):
        """Log status change"""
        self.log(
            action="STATUS_CHANGE",
            place_id=place_id,
            details={
                "old_status": old_status,
                "new_status": new_status,
                "reason": reason,
            },
            evidence_urls=evidence_urls
        )
    
    def log_export(
        self,
        place_id: str,
        fields_updated: list,
        dry_run: bool = False
    ):
        """Log export to JSON"""
        self.log(
            action="EXPORT" if not dry_run else "EXPORT_DRY_RUN",
            place_id=place_id,
            details={
                "fields_updated": fields_updated,
            }
        )
    
    def get_entries(self, place_id: Optional[str] = None) -> list:
        """Get audit entries, optionally filtered by place_id"""
        if place_id:
            return [e for e in self.entries if e["place_id"] == place_id]
        return self.entries


class PipelineMetrics:
    """Collect metrics for a pipeline run"""
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.started_at = datetime.utcnow()
        self.completed_at: Optional[datetime] = None
        
        # Counters
        self.sources_checked = 0
        self.places_extracted = 0
        self.places_validated = 0
        self.places_added = 0
        self.places_updated = 0
        self.places_flagged = 0
        
        # Timing
        self.stage_timings: Dict[str, float] = {}
        
        # Errors
        self.errors: list = []
    
    def record_stage_start(self, stage: str):
        """Record start of a stage"""
        self.stage_timings[f"{stage}_start"] = datetime.utcnow().timestamp()
    
    def record_stage_end(self, stage: str):
        """Record end of a stage"""
        start_key = f"{stage}_start"
        end_key = f"{stage}_end"
        self.stage_timings[end_key] = datetime.utcnow().timestamp()
        
        if start_key in self.stage_timings:
            duration = self.stage_timings[end_key] - self.stage_timings[start_key]
            self.stage_timings[f"{stage}_duration_sec"] = duration
    
    def add_error(self, error: str, context: Optional[Dict] = None):
        """Add an error to the log"""
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "error": error,
            "context": context or {},
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "run_id": self.run_id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": (
                (self.completed_at - self.started_at).total_seconds()
                if self.completed_at else None
            ),
            "sources_checked": self.sources_checked,
            "places_extracted": self.places_extracted,
            "places_validated": self.places_validated,
            "places_added": self.places_added,
            "places_updated": self.places_updated,
            "places_flagged": self.places_flagged,
            "stage_timings": self.stage_timings,
            "errors": self.errors,
        }
    
    def save(self):
        """Save metrics to file"""
        metrics_file = config.logs_dir / f"metrics_{self.run_id}.json"
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2, default=str)

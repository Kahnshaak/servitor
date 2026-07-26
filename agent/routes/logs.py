import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler

from fastapi import APIRouter, Request

from config import settings

router = APIRouter(prefix="/logs")

# Set up a rotating log file on the main server to store audit entries from the bot
os.makedirs(settings.log_dir, exist_ok=True)
_log_handler = RotatingFileHandler(
    os.path.join(settings.log_dir, "audit.log"),
    maxBytes=10 * 1024 * 1024,  # 10 MB
    backupCount=5,
)
_log_handler.setFormatter(logging.Formatter("%(message)s"))

_audit_logger = logging.getLogger("servitor.audit")
_audit_logger.setLevel(logging.INFO)
_audit_logger.addHandler(_log_handler)
_audit_logger.propagate = False


@router.post("/ingest")
async def ingest_logs(request: Request):
    body = await request.json()
    entries = body if isinstance(body, list) else [body]

    received_at = datetime.now(timezone.utc).isoformat()
    for entry in entries:
        entry["received_at"] = received_at
        _audit_logger.info(json.dumps(entry))

    return {"success": True, "ingested": len(entries)}

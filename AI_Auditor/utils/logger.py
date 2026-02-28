"""
logger.py — Centralized structured logging for the audit system.
Logs to both console (rich-formatted) and file (JSON + plain text).
"""

import logging
import logging.handlers
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure logs directory exists
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
JSON_LOG_FILE = LOGS_DIR / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"


class JSONFormatter(logging.Formatter):
    """Formats log records as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        reserved = {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message",
        }
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "thread_name": record.threadName,
        }

        extra_fields = {
            k: v for k, v in record.__dict__.items()
            if k not in reserved and not k.startswith("_")
        }
        if extra_fields:
            log_data["extra"] = extra_fields
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class PlainTextFormatter(logging.Formatter):
    """Formats log records as plain text with timestamps and context."""
    
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        level = record.levelname.ljust(8)
        
        # Add thread info for debugging concurrent operations
        thread_info = f"[{record.threadName}]" if record.threadName != "MainThread" else ""
        
        msg = f"{timestamp} {level} {record.name}:{record.funcName}({record.lineno}) {thread_info} {record.getMessage()}"
        
        if record.exc_info:
            msg += "\n" + self.formatException(record.exc_info)
        
        return msg


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure centralized logging for the audit system.
    
    Returns:
        logging.Logger: Main logger for the application.
    """
    
    # Root logger
    root_logger = logging.getLogger()
    root_level = logging.DEBUG if verbose else logging.INFO
    root_logger.setLevel(root_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # ─── File Handler (Plain Text) ────────────────────────────────────────
    file_handler = logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
    file_formatter = PlainTextFormatter()
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # ─── JSON Log Handler ─────────────────────────────────────────────────
    json_handler = logging.FileHandler(JSON_LOG_FILE, mode='w', encoding='utf-8')
    json_handler.setLevel(logging.DEBUG)
    json_formatter = JSONFormatter()
    json_handler.setFormatter(json_formatter)
    root_logger.addHandler(json_handler)
    
    # ─── Console Handler (Rich formatting) ────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not verbose else logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Get main application logger
    app_logger = logging.getLogger("AI_Auditor")
    
    # Log startup info
    app_logger.info(f"Logging initialized. Log files:")
    app_logger.info(f"  Plain text log: {LOG_FILE}")
    app_logger.info(f"  JSON log: {JSON_LOG_FILE}")
    app_logger.debug(f"Log level: {'DEBUG' if verbose else 'INFO'}")
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(f"AI_Auditor.{name}")


def log_event(
    logger: logging.Logger,
    event: str,
    level: int = logging.INFO,
    correlation_id: Optional[str] = None,
    **payload: object,
) -> None:
    extra: dict = {
        "audit_event": event,
        "audit_payload": payload,
    }
    if correlation_id:
        extra["correlation_id"] = correlation_id
    logger.log(level, event, extra=extra)

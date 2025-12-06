"""
Structured logging system using Loguru.
Provides JSON formatted logs with automatic rotation and retention.
"""

import sys
import json
from pathlib import Path
from loguru import logger
from .config import settings


def serialize(record: dict) -> str:
    """Serialize log record to JSON format."""
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add extra fields if present
    if record.get("extra"):
        subset["extra"] = record["extra"]
    
    # Add exception info if present
    if record.get("exception"):
        subset["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else None,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }
    
    return json.dumps(subset, ensure_ascii=False)


def format_record(record: dict) -> str:
    """Format log record based on settings."""
    if settings.LOG_FORMAT == "json":
        return serialize(record) + "\n"
    else:
        # Text format
        format_string = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>\n"
        )
        if record.get("exception"):
            format_string += "{exception}\n"
        return format_string


# Remove default handler
logger.remove()

# Add console handler (always in text format for readability)
logger.add(
    sys.stderr,
    level=settings.LOG_LEVEL,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    colorize=True,
    backtrace=True,
    diagnose=True,
)

# Add file handler with rotation
log_dir = Path(settings.LOG_DIR)
log_dir.mkdir(parents=True, exist_ok=True)

if settings.LOG_FORMAT == "json":
    # JSON format - use serialize
    logger.add(
        log_dir / "bidding_system_{time}.log",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        enqueue=True,
        backtrace=True,
        diagnose=True,
        serialize=True,
    )
else:
    # Text format - use format function
    logger.add(
        log_dir / "bidding_system_{time}.log",
        rotation=settings.LOG_ROTATION,
        retention=settings.LOG_RETENTION,
        level=settings.LOG_LEVEL,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

# Add error-specific log file
if settings.LOG_FORMAT == "json":
    logger.add(
        log_dir / "errors_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="ERROR",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        serialize=True,
    )
else:
    logger.add(
        log_dir / "errors_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="ERROR",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )


# Utility functions for structured logging
def log_request(method: str, path: str, **kwargs):
    """Log HTTP request."""
    logger.info(f"Request: {method} {path}", extra=kwargs)


def log_response(status_code: int, duration: float, **kwargs):
    """Log HTTP response."""
    logger.info(f"Response: {status_code} ({duration:.2f}s)", extra=kwargs)


def log_task_start(task_name: str, task_id: str, **kwargs):
    """Log task start."""
    logger.info(f"Task started: {task_name} [{task_id}]", extra=kwargs)


def log_task_complete(task_name: str, task_id: str, duration: float, **kwargs):
    """Log task completion."""
    logger.info(f"Task completed: {task_name} [{task_id}] ({duration:.2f}s)", extra=kwargs)


def log_task_error(task_name: str, task_id: str, error: Exception, **kwargs):
    """Log task error."""
    logger.error(f"Task failed: {task_name} [{task_id}]", extra=kwargs, exception=error)


__all__ = [
    "logger",
    "log_request",
    "log_response",
    "log_task_start",
    "log_task_complete",
    "log_task_error",
]

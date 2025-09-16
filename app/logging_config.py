"""
Logging configuration for OttoMate API.
Provides structured logging for both local development and Google Cloud.
"""

import logging
import os
import sys
from typing import Dict, Any

def setup_logging() -> logging.Logger:
    """
    Configure logging for the application.

    - Local development: Colored console output
    - Google Cloud: Structured JSON logs for Cloud Logging

    Returns:
        Configured logger instance
    """

    # Determine if running in Google Cloud
    is_cloud = os.getenv('K_SERVICE') is not None or os.getenv('GOOGLE_CLOUD_PROJECT') is not None

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    if is_cloud:
        # Cloud Logging - JSON structured format
        formatter = StructuredFormatter()
    else:
        # Local Development - Human readable format
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create application logger
    app_logger = logging.getLogger('ottomate')

    return app_logger

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured logging in Google Cloud.
    Outputs JSON format compatible with Cloud Logging.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry = {
            'timestamp': self.formatTime(record),
            'severity': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)

        # Add any extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)

        return json.dumps(log_entry)

def log_api_request(endpoint: str, method: str, status_code: int, duration_ms: float, user_id: str = None):
    """
    Log API request with structured data for monitoring.

    Args:
        endpoint: API endpoint path
        method: HTTP method
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        user_id: User identifier (optional)
    """
    logger = logging.getLogger('ottomate.api')

    extra_fields = {
        'endpoint': endpoint,
        'method': method,
        'status_code': status_code,
        'duration_ms': duration_ms,
        'request_type': 'api_request'
    }

    if user_id:
        extra_fields['user_id'] = user_id

    # Create log record with extra fields
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname='',
        lineno=0,
        msg=f"{method} {endpoint} - {status_code} ({duration_ms:.2f}ms)",
        args=(),
        exc_info=None
    )
    record.extra_fields = extra_fields

    logger.handle(record)

def log_blueprint_generation(brief_id: str, success: bool, duration_ms: float, error: str = None):
    """
    Log blueprint generation events for monitoring and debugging.

    Args:
        brief_id: Brief identifier
        success: Whether generation succeeded
        duration_ms: Generation duration in milliseconds
        error: Error message if failed
    """
    logger = logging.getLogger('ottomate.blueprint')

    extra_fields = {
        'brief_id': brief_id,
        'success': success,
        'duration_ms': duration_ms,
        'operation': 'blueprint_generation'
    }

    if error:
        extra_fields['error'] = error

    message = f"Blueprint generation {'succeeded' if success else 'failed'} for brief {brief_id}"
    if error:
        message += f": {error}"

    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO if success else logging.ERROR,
        pathname='',
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    record.extra_fields = extra_fields

    logger.handle(record)

# Initialize logging when module is imported
setup_logging()
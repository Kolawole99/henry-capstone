"""
Centralized logging configuration for Nexus-Mind application.

Provides structured JSON logging with rotating file handlers and integration
with Langfuse trace IDs for request correlation.
"""

import logging
import logging.handlers
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
trace_id_var: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)

# Log directory
LOG_DIR = Path(__file__).parent.parent.parent.parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    Includes request_id and trace_id from context variables.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request ID if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        # Add trace ID if available
        trace_id = trace_id_var.get()
        if trace_id:
            log_data["trace_id"] = trace_id
        
        # Add extra fields from record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, default=str)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Initialize logging configuration with rotating file handlers.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    json_formatter = JSONFormatter()
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # App log file (all logs INFO and above)
    app_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    root_logger.addHandler(app_handler)
    
    # Error log file (ERROR and above only)
    error_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "error.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)
    
    # Request log file (for HTTP requests/responses)
    request_logger = logging.getLogger("nexus.requests")
    request_logger.setLevel(logging.INFO)
    request_logger.propagate = False  # Don't propagate to root logger
    
    request_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "requests.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    request_handler.setFormatter(json_formatter)
    request_logger.addHandler(request_handler)
    
    # Agent log file (for agent execution)
    agent_logger = logging.getLogger("nexus.agents")
    agent_logger.setLevel(logging.INFO)
    agent_logger.propagate = True  # Also send to root logger
    
    agent_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "agents.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8"
    )
    agent_handler.setFormatter(json_formatter)
    agent_logger.addHandler(agent_handler)
    
    # Log initialization
    root_logger.info("Logging system initialized", extra={
        'extra_fields': {
            'log_level': log_level,
            'log_dir': str(LOG_DIR)
        }
    })


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    request_id_var.set(request_id)


def get_request_id() -> Optional[str]:
    """Get the request ID from the current context."""
    return request_id_var.get()


def set_trace_id(trace_id: str) -> None:
    """Set the Langfuse trace ID for the current context."""
    trace_id_var.set(trace_id)


def get_trace_id() -> Optional[str]:
    """Get the Langfuse trace ID from the current context."""
    return trace_id_var.get()


def log_with_context(logger: logging.Logger, level: int, message: str, **kwargs) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.ERROR, etc.)
        message: Log message
        **kwargs: Additional fields to include in the log
    """
    extra = {'extra_fields': kwargs}
    logger.log(level, message, extra=extra)


# Convenience functions for common logging patterns

def log_request(
    method: str,
    path: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log an HTTP request/response.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: Response status code
        duration_ms: Request duration in milliseconds
        **kwargs: Additional fields (client_ip, user_agent, etc.)
    """
    logger = logging.getLogger("nexus.requests")
    
    log_data = {
        "method": method,
        "path": path,
    }
    
    if status_code is not None:
        log_data["status_code"] = status_code
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    log_data.update(kwargs)
    
    message = f"{method} {path}"
    if status_code:
        message += f" - {status_code}"
    
    log_with_context(logger, logging.INFO, message, **log_data)


def log_agent_execution(
    agent_name: str,
    operation: str,
    duration_ms: Optional[float] = None,
    **kwargs
) -> None:
    """
    Log an agent execution.
    
    Args:
        agent_name: Name of the agent (coordinator, dispatcher, etc.)
        operation: Operation being performed
        duration_ms: Operation duration in milliseconds
        **kwargs: Additional fields (query, result, confidence, etc.)
    """
    logger = logging.getLogger("nexus.agents")
    
    log_data = {
        "agent": agent_name,
        "operation": operation,
    }
    
    if duration_ms is not None:
        log_data["duration_ms"] = round(duration_ms, 2)
    
    log_data.update(kwargs)
    
    message = f"{agent_name} - {operation}"
    
    log_with_context(logger, logging.INFO, message, **log_data)


def log_error(
    error: Exception,
    context: str,
    **kwargs
) -> None:
    """
    Log an error with context.
    
    Args:
        error: Exception instance
        context: Description of where/when the error occurred
        **kwargs: Additional context fields
    """
    logger = logging.getLogger("nexus.errors")
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
    }
    log_data.update(kwargs)
    
    message = f"{context}: {type(error).__name__} - {str(error)}"
    
    logger.error(message, exc_info=True, extra={'extra_fields': log_data})

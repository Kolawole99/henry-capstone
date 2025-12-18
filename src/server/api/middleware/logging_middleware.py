"""
FastAPI middleware for automatic request/response logging.
"""

import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ...utils.logger import (
    set_request_id,
    get_request_id,
    log_request,
    get_logger
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Automatically:
    - Generates unique request IDs
    - Logs incoming requests with metadata
    - Logs outgoing responses with status and duration
    - Captures and logs exceptions
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Log incoming request
        start_time = time.time()
        
        logger.info(
            f"Incoming request: {request.method} {request.url.path}",
            extra={
                'extra_fields': {
                    'request_id': request_id,
                    'method': request.method,
                    'path': request.url.path,
                    'query_params': dict(request.query_params),
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                }
            }
        )
        
        # Process request and capture response
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            log_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
                user_agent=user_agent,
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    'extra_fields': {
                        'request_id': request_id,
                        'method': request.method,
                        'path': request.url.path,
                        'duration_ms': round(duration_ms, 2),
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'client_ip': client_ip,
                    }
                }
            )
            
            # Re-raise the exception to be handled by FastAPI
            raise

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable, Awaitable

from fastapi import HTTPException, Request, status
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple in-memory rate limiter.
    
    This is a basic implementation for development. For production,
    consider using Redis-based rate limiting.
    """
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: dict[str, list[float]] = defaultdict(list)
        self._cleanup_interval = 60  # Clean up old entries every 60 seconds
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self) -> None:
        """Remove entries older than 1 minute."""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        cutoff_time = current_time - 60
        for key in list(self.requests.keys()):
            self.requests[key] = [
                timestamp for timestamp in self.requests[key]
                if timestamp > cutoff_time
            ]
            if not self.requests[key]:
                del self.requests[key]
        
        self._last_cleanup = current_time
    
    def _get_client_id(self, request: Request) -> str:
        """Get client identifier from request (IP address)."""
        # Try to get real IP from proxy headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        return request.client.host if request.client else "unknown"
    
    def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed based on rate limit."""
        self._cleanup_old_entries()
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Remove requests older than 1 minute
        cutoff_time = current_time - 60
        self.requests[client_id] = [
            timestamp for timestamp in self.requests[client_id]
            if timestamp > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(self.requests[client_id]) >= self.requests_per_minute:
            return False
        
        # Add current request
        self.requests[client_id].append(current_time)
        return True


async def rate_limit_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    rate_limiter: RateLimiter,
) -> Response:
    """Rate limiting middleware.
    
    Returns 429 Too Many Requests if rate limit is exceeded.
    """
    # Skip rate limiting for health and metrics endpoints
    if request.url.path in ["/v1/health", "/health", "/metrics"]:
        return await call_next(request)
    
    if not rate_limiter.is_allowed(request):
        logger.warning(
            f"Rate limit exceeded for client {rate_limiter._get_client_id(request)}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {rate_limiter.requests_per_minute} requests per minute."
        )
    
    return await call_next(request)


async def jwt_auth_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
    jwt_secret: str | None,
    jwt_algorithm: str = "HS256",
) -> Response:
    """JWT authentication middleware.
    
    Validates JWT tokens from Authorization header if JWT is enabled.
    If jwt_secret is None, authentication is disabled.
    """
    # Skip authentication if not configured
    if jwt_secret is None:
        return await call_next(request)
    
    # Skip authentication for health and metrics endpoints
    if request.url.path in ["/v1/health", "/health", "/metrics"]:
        return await call_next(request)
    
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Parse Bearer token
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Validate token using PyJWT
    try:
        import jwt  # type: ignore[import-untyped]
    except ImportError:
        logger.error(
            "JWT authentication enabled but PyJWT not installed. "
            "Install with: pip install 'datafusion-ml[auth]' or pip install PyJWT"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT authentication not properly configured. PyJWT library required."
        )
    
    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=[jwt_algorithm],
        )
        # Attach user info to request state for use in route handlers
        request.state.user = payload  # type: ignore[attr-defined]
        
    except jwt.ExpiredSignatureError:  # type: ignore[name-defined]
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:  # type: ignore[name-defined]
        logger.debug(f"Invalid JWT token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await call_next(request)

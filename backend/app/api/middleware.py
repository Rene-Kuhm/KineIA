import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter: 100 requests per hour per user/IP.

    Uses a sliding window approach with request timestamps per client.
    """

    RATE_LIMIT = 100
    WINDOW_SECONDS = 3600  # 1 hour

    def __init__(self, app):
        super().__init__(app)
        self._store: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        """Derive client identifier: user_id from auth header, else client IP."""
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # Use token prefix as user key (simplified — avoids parsing JWT in middleware)
            # For uniqueness, use first 20 chars of token + IP
            token_segment = auth_header.split(" ", 1)[1][:20]
            client_ip = request.client.host if request.client else "unknown"
            return f"user:{token_segment}:{client_ip}"

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    async def dispatch(self, request: Request, call_next) -> Response:
        key = self._client_key(request)
        now = time.time()

        # Prune old timestamps outside the window
        window_start = now - self.WINDOW_SECONDS
        self._store[key] = [ts for ts in self._store[key] if ts > window_start]

        if len(self._store[key]) >= self.RATE_LIMIT:
            retry_after = int(self.WINDOW_SECONDS - (now - self._store[key][0]))
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "message": f"Rate limit exceeded. {self.RATE_LIMIT} requests per hour.",
                },
                headers={"Retry-After": str(max(1, retry_after))},
            )

        self._store[key].append(now)
        response = await call_next(request)
        return response

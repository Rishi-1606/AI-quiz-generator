"""
Shared rate-limiter instance.

Defined in its own module to avoid the circular import that would occur
if routers imported `limiter` directly from `app.main`
(main imports routers, routers would import main → cycle).
"""

from fastapi import Request
import jwt

from app.config import SECRET_KEY, ALGORITHM
from slowapi import Limiter


def _get_user_id_key(request: Request) -> str:
    """
    Rate-limit key: user account ID decoded from the JWT Bearer token.
    Falls back to remote IP if the token is absent or invalid.
    """
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except Exception:
            pass
    return request.client.host if request.client else "unknown"


# Single shared limiter — imported by main.py AND the routers
limiter = Limiter(key_func=_get_user_id_key)

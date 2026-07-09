from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import get_db
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def create_access_token(data: dict) -> str:
    """Create a JWT access token with an expiration time."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    print(f"[DEBUG] Created token for data={data}, token={encoded_jwt[:30]}...")
    return encoded_jwt


def get_current_user(
    request: Request,
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency that decodes a JWT token and returns the current user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Debug: log what we received
    auth_header = request.headers.get("authorization", "")
    print(f"[DEBUG] /me called - OAuth2 token: {token[:30] if token else 'None'}, Auth header: {auth_header[:50] if auth_header else 'MISSING'}")

    # If OAuth2PasswordBearer didn't extract the token, try the raw header
    if not token:
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            print(f"[DEBUG] Extracted token from raw header: {token[:30]}...")
        else:
            print(f"[DEBUG] No token found anywhere! Raising 401.")
            raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_raw = payload.get("sub")
        print(f"[DEBUG] Token decoded successfully. user_id_raw={user_id_raw}, type={type(user_id_raw)}")
        if user_id_raw is None:
            print(f"[DEBUG] user_id is None! Full payload: {payload}")
            raise credentials_exception
        user_id = int(user_id_raw)
    except (jwt.ExpiredSignatureError, ValueError):
        print(f"[DEBUG] Token expired or value error converting sub to int!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        print(f"[DEBUG] Invalid token error: {e}")
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    print(f"[DEBUG] DB query for user_id={user_id}: found={'YES' if user else 'NO'}")
    if user is None:
        raise credentials_exception

    return user

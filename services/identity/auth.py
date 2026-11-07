"""Lightweight JWT & OAuth2 Security Layer for Local Dev, CI, and Keycloak-compatible claims."""

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import jwt
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from services.common.config import settings

security_bearer = HTTPBearer(auto_error=False)


class UserProfile(BaseModel):
    """Authenticated user profile with role claims."""
    id: str
    username: str
    email: str
    roles: List[str] = Field(default_factory=list)
    customer_id: Optional[str] = None


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """Generate PBKDF2 HMAC-SHA256 password hash."""
    salt = salt or secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against salt$hash string."""
    try:
        salt, key_hex = hashed_password.split("$")
        test_key = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100000
        )
        return hmac.compare_digest(key_hex, test_key.hex())
    except Exception:
        return False


def create_access_token(
    user_id: str,
    username: str,
    email: str,
    roles: List[str],
    customer_id: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create signed HS256 JWT access token with Keycloak-compatible realm_access claims."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    payload: Dict[str, Any] = {
        "sub": user_id,
        "preferred_username": username,
        "email": email,
        "customer_id": customer_id,
        "realm_access": {"roles": roles},
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "iss": "aegis-meridian-auth",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate JWT access token."""
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer="aegis-meridian-auth",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
) -> UserProfile:
    """FastAPI dependency to extract current authenticated user."""
    # Development bypass if no credentials provided in development mode
    if not credentials:
        if settings.ENVIRONMENT == "development":
            return UserProfile(
                id="dev_user_admin",
                username="admin_dev",
                email="admin@meridian.local",
                roles=["admin", "ops_analyst", "compliance_officer", "customer"],
                customer_id="cust_dev_001",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    roles = payload.get("roles") or payload.get("realm_access", {}).get("roles", [])
    return UserProfile(
        id=payload["sub"],
        username=payload.get("preferred_username", ""),
        email=payload.get("email", ""),
        roles=roles,
        customer_id=payload.get("customer_id"),
    )


def require_role(allowed_roles: List[str]):
    """Role-based authorization dependency factory."""
    async def role_checker(user: UserProfile = Depends(get_current_user)) -> UserProfile:
        if "admin" in user.roles:
            return user
        if not any(role in user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of roles: {allowed_roles}",
            )
        return user
    return role_checker

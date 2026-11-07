"""Authentication and Identity REST API routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.identity.auth import (
    UserProfile,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["Identity & Auth"])

# In-memory mock user directory for fast local testing
MOCK_USERS = {
    "alice@example.com": {
        "id": "usr_alice_01",
        "username": "alice",
        "password_hash": hash_password("password123"),
        "roles": ["customer", "maker"],
        "customer_id": "cust_alice_01",
    },
    "bob@example.com": {
        "id": "usr_bob_02",
        "username": "bob",
        "password_hash": hash_password("password123"),
        "roles": ["customer", "approver"],
        "customer_id": "cust_bob_02",
    },
    "analyst@meridian.bank": {
        "id": "usr_analyst_03",
        "username": "sarah_analyst",
        "password_hash": hash_password("analyst123"),
        "roles": ["ops_analyst", "compliance_officer"],
        "customer_id": None,
    },
    "admin@meridian.bank": {
        "id": "usr_admin_00",
        "username": "super_admin",
        "password_hash": hash_password("admin123"),
        "roles": ["admin", "ops_analyst", "compliance_officer"],
        "customer_id": None,
    },
}


class LoginRequest(BaseModel):
    """User login request."""
    email: str
    password: str


class TokenResponse(BaseModel):
    """JWT Token exchange response."""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int = 3600
    user: UserProfile


class DevTokenRequest(BaseModel):
    """Developer helper to issue a token with arbitrary roles."""
    username: str = "dev_user"
    email: str = "dev@example.com"
    roles: List[str] = Field(default=["customer", "maker", "approver"])
    customer_id: Optional[str] = "cust_dev_01"


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login with email and password to receive JWT access token",
)
async def login(request: LoginRequest) -> TokenResponse:
    user_record = MOCK_USERS.get(request.email)
    if not user_record or not verify_password(request.password, user_record["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_profile = UserProfile(
        id=user_record["id"],
        username=user_record["username"],
        email=request.email,
        roles=user_record["roles"],
        customer_id=user_record["customer_id"],
    )

    token = create_access_token(
        user_id=user_profile.id,
        username=user_profile.username,
        email=user_profile.email,
        roles=user_profile.roles,
        customer_id=user_profile.customer_id,
    )

    return TokenResponse(access_token=token, user=user_profile)


@router.post(
    "/dev-token",
    response_model=TokenResponse,
    summary="Generate a custom development JWT token for testing squads and roles",
)
async def generate_dev_token(request: DevTokenRequest) -> TokenResponse:
    user_profile = UserProfile(
        id=f"dev_{request.username}",
        username=request.username,
        email=request.email,
        roles=request.roles,
        customer_id=request.customer_id,
    )
    token = create_access_token(
        user_id=user_profile.id,
        username=user_profile.username,
        email=user_profile.email,
        roles=user_profile.roles,
        customer_id=user_profile.customer_id,
    )
    return TokenResponse(access_token=token, user=user_profile)


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get authenticated user profile and roles",
)
async def get_me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user

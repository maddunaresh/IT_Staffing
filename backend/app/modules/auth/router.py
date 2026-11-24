from fastapi import APIRouter, Depends, HTTPException

from app.core.security import create_access_token
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import LoginRequest, LoginResponse, UserProfile
from app.modules.auth.service import authenticate

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    user = authenticate(request.email, request.password)

    if user is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return LoginResponse(
        access_token=create_access_token(user.user_id),
        user=user,
    )


@router.get("/me", response_model=UserProfile)
def me(user: UserProfile = Depends(get_current_user)) -> UserProfile:
    return user
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import text

from app.core.security import decode_access_token
from app.db.session import engine
from app.modules.auth.schemas import UserProfile

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> UserProfile:
    unauthorized = HTTPException(
        status_code=401,
        detail="Missing or invalid access token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise unauthorized

    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized from None

    with engine.connect() as connection:
        user = connection.execute(
            text("""
                SELECT user_id, full_name, email
                FROM dbo.Users
                WHERE user_id = :user_id AND is_active = 1
            """),
            {"user_id": user_id},
        ).mappings().one_or_none()

        if user is None:
            raise unauthorized

        roles = connection.execute(
            text("""
                SELECT r.role_name
                FROM dbo.UserRoles AS ur
                JOIN dbo.Roles AS r ON r.role_id = ur.role_id
                WHERE ur.user_id = :user_id
                ORDER BY r.role_name
            """),
            {"user_id": user_id},
        ).scalars().all()

    return UserProfile(**user, roles=list(roles))
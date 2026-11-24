from pwdlib import PasswordHash
from sqlalchemy import text

from app.db.session import engine
from app.modules.auth.schemas import UserProfile

password_hasher = PasswordHash.recommended()
dummy_hash = password_hasher.hash("unused-password-for-timing-check")


def authenticate(email: str, password: str) -> UserProfile | None:
    with engine.connect() as connection:
        user = connection.execute(
            text("""
                SELECT user_id, full_name, email, password_hash, is_active
                FROM dbo.Users
                WHERE email = :email
            """),
            {"email": email.strip().lower()},
        ).mappings().one_or_none()

        stored_hash = user["password_hash"] if user is not None else dummy_hash
        password_matches = password_hasher.verify(password, stored_hash)

        if user is None or not user["is_active"] or not password_matches:
            return None

        roles = connection.execute(
            text("""
                SELECT r.role_name
                FROM dbo.UserRoles AS ur
                JOIN dbo.Roles AS r ON r.role_id = ur.role_id
                WHERE ur.user_id = :user_id
                ORDER BY r.role_name
            """),
            {"user_id": user["user_id"]},
        ).scalars().all()

        return UserProfile(
            user_id=user["user_id"],
            full_name=user["full_name"],
            email=user["email"],
            roles=list(roles),
        )
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import column, select, table, text
from sqlalchemy.exc import IntegrityError

from app.db.session import engine
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserProfile
from app.modules.auth.service import password_hasher

router = APIRouter(prefix="/admin", tags=["Admin Users"])


class CreateUserRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=150, pattern=r"\S")
    email: EmailStr
    password: str = Field(min_length=10, max_length=256)
    role: Literal["Manager", "Recruiter", "Bench Sales Marketer"]


class StaffListItem(BaseModel):
    full_name: str
    login_id: int
    email: EmailStr

# Query definitions for the existing SQL Server tables.
users_table = table(
    "Users",
    column("user_id"),
    column("full_name"),
    column("email"),
    schema="dbo",
)

user_roles_table = table(
    "UserRoles",
    column("user_id"),
    column("role_id"),
    schema="dbo",
)

roles_table = table(
    "Roles",
    column("role_id"),
    column("role_name"),
    schema="dbo",
)


def require_super_admin(
    current_user: UserProfile = Depends(get_current_user),
) -> None:
    if "Super Admin" not in current_user.roles:
        raise HTTPException(
            status_code=403,
            detail="Super Admin access required",
        )


@router.post(
    "/users",
    response_model=UserProfile,
    status_code=201,
    dependencies=[Depends(require_super_admin)],
)
def create_user(request: CreateUserRequest) -> UserProfile:
    full_name = request.full_name.strip()
    email = request.email.lower()
    password_hash = password_hasher.hash(request.password)

    try:
        with engine.begin() as connection:
            role_id = connection.execute(
                text("SELECT role_id FROM dbo.Roles WHERE role_name = :role"),
                {"role": request.role},
            ).scalar_one_or_none()

            if role_id is None:
                raise HTTPException(
                    status_code=409,
                    detail="This role has not been configured in SQL Server",
                )

            user_id = connection.execute(
                text("""
                    INSERT INTO dbo.Users (full_name, email, password_hash)
                    OUTPUT INSERTED.user_id
                    VALUES (:full_name, :email, :password_hash)
                """),
                {
                    "full_name": full_name,
                    "email": email,
                    "password_hash": password_hash,
                },
            ).scalar_one()

            connection.execute(
                text("""
                    INSERT INTO dbo.UserRoles (user_id, role_id)
                    VALUES (:user_id, :role_id)
                """),
                {"user_id": user_id, "role_id": role_id},
            )
    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="Account could not be created. Check whether the email is already in use.",
        ) from exc

    return UserProfile(
        user_id=user_id,
        full_name=full_name,
        email=email,
        roles=[request.role],
    )


def list_staff_by_role(role_name: str) -> list[StaffListItem]:
    staff_with_roles = users_table.join(
        user_roles_table,
        users_table.c.user_id == user_roles_table.c.user_id,
    ).join(
        roles_table,
        user_roles_table.c.role_id == roles_table.c.role_id,
    )

    statement = (
        select(
            users_table.c.full_name,
            users_table.c.user_id.label("login_id"),
            users_table.c.email,
        )
        .select_from(staff_with_roles)
        .where(roles_table.c.role_name == role_name)
        .order_by(users_table.c.full_name, users_table.c.email)
    )

    with engine.connect() as connection:
        rows = connection.execute(statement).mappings()
        return [StaffListItem(**row) for row in rows]


@router.get(
    "/recruiters",
    response_model=list[StaffListItem],
    dependencies=[Depends(require_super_admin)],
)
def get_recruiters() -> list[StaffListItem]:
    return list_staff_by_role("Recruiter")


@router.get(
    "/marketers",
    response_model=list[StaffListItem],
    dependencies=[Depends(require_super_admin)],
)
def get_marketers() -> list[StaffListItem]:
    return list_staff_by_role("Bench Sales Marketer")
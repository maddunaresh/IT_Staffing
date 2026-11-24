from getpass import getpass

from email_validator import EmailNotValidError, validate_email
from pwdlib import PasswordHash
from sqlalchemy import text

from app.db.session import engine


def main():
    try:
        email = validate_email(
            input("Admin email: ").strip(),
            check_deliverability=False,
        ).normalized.lower()
    except EmailNotValidError as exc:
        raise SystemExit(str(exc)) from exc

    password = getpass("Admin password (at least 15 characters): ")
    if len(password) < 15:
        raise SystemExit("Use at least 15 characters.")
    if password != getpass("Confirm password: "):
        raise SystemExit("Passwords do not match.")

    password_hash = PasswordHash.recommended().hash(password)

    with engine.begin() as connection:
        role_id = connection.execute(
            text("SELECT role_id FROM dbo.Roles WHERE role_name = :role"),
            {"role": "Super Admin"},
        ).scalar_one_or_none()

        if role_id is None:
            raise SystemExit("The Super Admin role is missing in SQL Server.")

        existing_user_id = connection.execute(
            text("SELECT user_id FROM dbo.Users WHERE email = :email"),
            {"email": email},
        ).scalar_one_or_none()

        if existing_user_id is not None:
            raise SystemExit("An account with this email already exists.")

        user_id = connection.execute(
            text("""
                INSERT INTO dbo.Users (full_name, email, password_hash)
                OUTPUT INSERTED.user_id
                VALUES (:full_name, :email, :password_hash)
            """),
            {
                "full_name": "System Administrator",
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

    print(f"Super Admin account created for {email}.")


if __name__ == "__main__":
    main()
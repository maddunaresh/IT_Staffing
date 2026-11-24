from datetime import datetime

from sqlalchemy import ForeignKey, Integer, LargeBinary, Unicode, UnicodeText, func
from sqlalchemy.dialects.mssql import BIT, DATETIME2
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class RecruitingBase(DeclarativeBase):
    pass


class ExistingUser(RecruitingBase):
    """Reference to the Users table already created for login."""

    __tablename__ = "Users"
    __table_args__ = {"schema": "dbo"}

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)


class Consultant(RecruitingBase):
    __tablename__ = "Consultants"
    __table_args__ = {"schema": "dbo"}

    consultant_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    recruiter_id: Mapped[int] = mapped_column(
        ForeignKey("dbo.Users.user_id"), index=True
    )
    email: Mapped[str] = mapped_column(Unicode(254), unique=True)
    first_name: Mapped[str] = mapped_column(Unicode(100))
    last_name: Mapped[str] = mapped_column(Unicode(100))
    primary_contact_number: Mapped[str] = mapped_column(Unicode(30))
    profile_json: Mapped[str] = mapped_column(UnicodeText)
    is_hotlisted: Mapped[bool] = mapped_column(BIT, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DATETIME2, server_default=func.sysutcdatetime()
    )


class ConsultantDocument(RecruitingBase):
    __tablename__ = "ConsultantDocuments"
    __table_args__ = {"schema": "dbo"}

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    consultant_id: Mapped[int] = mapped_column(
        ForeignKey("dbo.Consultants.consultant_id"), index=True
    )
    file_name: Mapped[str] = mapped_column(Unicode(255))
    content_type: Mapped[str] = mapped_column(Unicode(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    file_content: Mapped[bytes] = mapped_column(LargeBinary)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("dbo.Users.user_id"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DATETIME2, server_default=func.sysutcdatetime()
    )
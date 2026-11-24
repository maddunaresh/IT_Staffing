from sqlalchemy import Integer, Unicode
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class LookupBase(DeclarativeBase):
    pass


class Skill(LookupBase):
    __tablename__ = "Skills"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column("skill_id", Integer, primary_key=True)
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    name_key: Mapped[str] = mapped_column(Unicode(256), unique=True, nullable=False)


class WorkAuthorization(LookupBase):
    __tablename__ = "WorkAuthorizations"
    __table_args__ = {"schema": "dbo"}

    id: Mapped[int] = mapped_column(
        "work_authorization_id", Integer, primary_key=True
    )
    name: Mapped[str] = mapped_column(Unicode(100), nullable=False)
    name_key: Mapped[str] = mapped_column(Unicode(256), unique=True, nullable=False)
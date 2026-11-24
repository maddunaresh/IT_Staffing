import json
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserProfile
from app.modules.lookups.models import Skill, WorkAuthorization
from app.modules.recruiting.models import Consultant, ConsultantDocument
from app.modules.recruiting.schemas import ConsultantInput


router = APIRouter(tags=["Recruiting"])

CurrentUser = Annotated[UserProfile, Depends(get_current_user)]

MANAGEMENT = {"Super Admin", "Manager"}
RECRUITING = MANAGEMENT | {"Recruiter"}

PROFILE_COLUMNS = (
    "email",
    "first_name",
    "last_name",
    "primary_contact_number",
)


def get_db():
    with Session(engine) as db:
        yield db


Database = Annotated[Session, Depends(get_db)]


def require_role(user: UserProfile, allowed: set[str]) -> None:
    if not allowed.intersection(user.roles):
        raise HTTPException(
            status_code=403,
            detail="You do not have permission for this action",
        )


def visible_consultants(user: UserProfile):
    require_role(user, RECRUITING)

    statement = select(Consultant)

    if not MANAGEMENT.intersection(user.roles):
        statement = statement.where(
            Consultant.recruiter_id == user.user_id
        )

    return statement


def find_consultant(
    db: Session,
    user: UserProfile,
    consultant_id: int,
    *,
    for_update: bool = False,
) -> Consultant:
    statement = visible_consultants(user).where(
        Consultant.consultant_id == consultant_id
    )

    if for_update:
        statement = statement.with_hint(
            Consultant,
            "WITH (UPDLOCK)",
            "mssql",
        )

    consultant = db.scalars(statement).one_or_none()

    if consultant is None:
        raise HTTPException(
            status_code=404,
            detail="Consultant not found",
        )

    return consultant


def profile_fields(consultant: Consultant) -> dict:
    profile = json.loads(consultant.profile_json)

    # Older profiles may contain these fields.
    profile.pop("technologies", None)
    profile.pop("work_authorization", None)
    profile.pop("skill_ids", None)

    return {
        **profile,
        **{
            field: getattr(consultant, field)
            for field in PROFILE_COLUMNS
        },
    }


def summary(consultant: Consultant) -> dict:
    return {
        "consultant_id": consultant.consultant_id,
        "recruiter_id": consultant.recruiter_id,
        **{
            field: getattr(consultant, field)
            for field in PROFILE_COLUMNS
        },
        "is_hotlisted": consultant.is_hotlisted,
        "created_at": consultant.created_at,
    }


def validate_lookup_ids(
    db: Session,
    profile: ConsultantInput,
) -> None:
    skill = db.get(Skill, profile.skill_id)

    if skill is None:
        raise HTTPException(
            status_code=422,
            detail="Unknown skill_id",
        )

    if profile.work_authorization_id is not None:
        authorization = db.get(
            WorkAuthorization,
            profile.work_authorization_id,
        )

        if authorization is None:
            raise HTTPException(
                status_code=422,
                detail="Unknown work_authorization_id",
            )


def apply_profile(
    consultant: Consultant,
    profile: ConsultantInput,
) -> None:
    values = profile.model_dump(mode="json")
    values["email"] = values["email"].lower()

    for field in PROFILE_COLUMNS:
        setattr(consultant, field, values.pop(field))

    consultant.profile_json = json.dumps(values)


def save_profile(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Could not save the profile. "
                "Check whether the email is already in use."
            ),
        ) from exc


@router.post("/consultants", status_code=201)
def add_consultant(
    profile: ConsultantInput,
    user: CurrentUser,
    db: Database,
):
    require_role(user, RECRUITING)
    validate_lookup_ids(db, profile)

    consultant = Consultant(recruiter_id=user.user_id)
    apply_profile(consultant, profile)

    db.add(consultant)
    save_profile(db)
    db.refresh(consultant)

    return {"consultant_id": consultant.consultant_id}


def list_consultants(
    db: Session,
    user: UserProfile,
    offset: int,
    limit: int,
    search: str = "",
    hotlisted: bool | None = None,
):
    statement = visible_consultants(user)

    if hotlisted is not None:
        statement = statement.where(
            Consultant.is_hotlisted == hotlisted
        )

    if search:
        statement = statement.where(
            or_(
                Consultant.email.contains(search, autoescape=True),
                Consultant.first_name.contains(search, autoescape=True),
                Consultant.last_name.contains(search, autoescape=True),
            )
        )

    statement = (
        statement
        .order_by(Consultant.consultant_id.desc())
        .offset(offset)
        .limit(limit)
    )

    return [
        summary(consultant)
        for consultant in db.scalars(statement)
    ]


@router.get("/consultants")
def get_consultants(
    user: CurrentUser,
    db: Database,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: str = Query("", max_length=254),
    hotlisted: bool | None = None,
):
    return list_consultants(
        db,
        user,
        offset,
        limit,
        search,
        hotlisted,
    )


@router.get("/consultants/{consultant_id}")
def get_consultant(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
):
    consultant = find_consultant(db, user, consultant_id)

    return {
        **profile_fields(consultant),
        **summary(consultant),
    }


@router.patch("/consultants/{consultant_id}")
def update_consultant(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
    changes: dict[str, Any] = Body(...),
):
    if not changes:
        raise HTTPException(
            status_code=422,
            detail="Send at least one field to update",
        )

    consultant = find_consultant(
        db,
        user,
        consultant_id,
        for_update=True,
    )

    try:
        profile = ConsultantInput.model_validate(
            {
                **profile_fields(consultant),
                **changes,
            }
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=[
                {
                    "field": list(error["loc"]),
                    "message": error["msg"],
                }
                for error in exc.errors()
            ],
        ) from exc

    validate_lookup_ids(db, profile)
    apply_profile(consultant, profile)

    save_profile(db)
    db.refresh(consultant)

    return {
        **profile_fields(consultant),
        **summary(consultant),
    }


@router.post(
    "/consultants/{consultant_id}/documents",
    status_code=201,
)
def upload_document(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
    file: UploadFile = File(...),
):
    find_consultant(db, user, consultant_id)

    name = (
        (file.filename or "")
        .replace("\\", "/")
        .rsplit("/", 1)[-1]
    )

    if (
        not name
        or len(name) > 255
        or not name.lower().endswith(".pdf")
    ):
        raise HTTPException(
            status_code=422,
            detail="Choose a PDF file with a valid filename",
        )

    max_bytes = 5 * 1024 * 1024
    content = file.file.read(max_bytes + 1)

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail="PDF must be 5 MB or smaller",
        )

    if not content.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=422,
            detail="File does not have a PDF header",
        )

    document = ConsultantDocument(
        consultant_id=consultant_id,
        file_name=name,
        content_type="application/pdf",
        size_bytes=len(content),
        file_content=content,
        uploaded_by=user.user_id,
    )

    db.add(document)
    db.flush()

    document_id = document.document_id
    db.commit()

    return {
        "document_id": document_id,
        "file_name": name,
    }


@router.get("/consultants/{consultant_id}/documents")
def get_documents(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
):
    find_consultant(db, user, consultant_id)

    statement = (
        select(
            ConsultantDocument.document_id,
            ConsultantDocument.file_name,
            ConsultantDocument.content_type,
            ConsultantDocument.size_bytes,
            ConsultantDocument.uploaded_by,
            ConsultantDocument.uploaded_at,
        )
        .where(
            ConsultantDocument.consultant_id == consultant_id
        )
        .order_by(
            ConsultantDocument.document_id.desc()
        )
    )

    return [
        dict(row)
        for row in db.execute(statement).mappings()
    ]




def set_hotlist(
    db: Session,
    user: UserProfile,
    consultant_id: int,
    hotlisted: bool,
):
    consultant = find_consultant(
        db,
        user,
        consultant_id,
        for_update=True,
    )

    consultant.is_hotlisted = hotlisted
    db.commit()

    return {
        "consultant_id": consultant_id,
        "is_hotlisted": hotlisted,
    }


@router.put("/hotlist/{consultant_id}")
def add_to_hotlist(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
):
    return set_hotlist(db, user, consultant_id, True)


@router.delete("/hotlist/{consultant_id}")
def remove_from_hotlist(
    consultant_id: int,
    user: CurrentUser,
    db: Database,
):
    return set_hotlist(db, user, consultant_id, False)


@router.get("/hotlist")
def get_hotlist(
    user: CurrentUser,
    db: Database,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return list_consultants(
        db,
        user,
        offset,
        limit,
        hotlisted=True,
    )
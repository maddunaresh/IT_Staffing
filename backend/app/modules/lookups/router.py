from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import engine
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserProfile
from app.modules.lookups.models import Skill, WorkAuthorization
from app.modules.lookups.states import US_STATES

router = APIRouter(prefix="/lookups", tags=["Shared Lookups"])
CurrentUser = Annotated[UserProfile, Depends(get_current_user)]


def get_db():
    with Session(engine) as db:
        yield db


Database = Annotated[Session, Depends(get_db)]


class LookupInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)


class LookupItem(BaseModel):
    id: int
    name: str


class StateItem(BaseModel):
    code: str
    name: str


def require_lookup_editor(user: CurrentUser) -> None:
    if not {"Manager", "Super Admin"}.intersection(user.roles):
        raise HTTPException(403, "Manager or Super Admin access required")


def add_lookup(db: Session, model, name: str) -> LookupItem:
    name = " ".join(name.split())
    key = name.casefold()
    if len(key) > 256:
        raise HTTPException(422, "Use a shorter name")

    item = model(name=name, name_key=key)
    try:
        db.add(item)
        db.flush()
        result = LookupItem(id=item.id, name=item.name)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        existing_id = db.scalar(select(model.id).where(model.name_key == key))
        if existing_id is not None:
            raise HTTPException(409, "This name already exists") from exc
        raise

    return result


@router.get("/skills", response_model=list[LookupItem])
def get_skills(user: CurrentUser, db: Database):
    return [
        LookupItem(id=item.id, name=item.name)
        for item in db.scalars(select(Skill).order_by(Skill.name))
    ]


@router.post(
    "/skills",
    response_model=LookupItem,
    status_code=201,
    dependencies=[Depends(require_lookup_editor)],
)
def add_skill(body: LookupInput, db: Database):
    return add_lookup(db, Skill, body.name)


@router.get("/work-authorizations", response_model=list[LookupItem])
def get_work_authorizations(user: CurrentUser, db: Database):
    return [
        LookupItem(id=item.id, name=item.name)
        for item in db.scalars(
            select(WorkAuthorization).order_by(WorkAuthorization.name)
        )
    ]


@router.post(
    "/work-authorizations",
    response_model=LookupItem,
    status_code=201,
    dependencies=[Depends(require_lookup_editor)],
)
def add_work_authorization(body: LookupInput, db: Database):
    return add_lookup(db, WorkAuthorization, body.name)


@router.get("/states", response_model=list[StateItem])
def get_states(user: CurrentUser):
    return [
        StateItem(code=code, name=name)
        for code, name in sorted(US_STATES.items(), key=lambda item: item[1])
    ]
from datetime import date
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.modules.lookups.states import validate_state_code


StateCode = Annotated[str, AfterValidator(validate_state_code)]
LookupId = Annotated[int, Field(strict=True, gt=0)]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Address(InputModel):
    street: str = Field(min_length=1, max_length=200)
    landmark: str | None = Field(None, max_length=150)
    city: str = Field(min_length=1, max_length=100)
    state: StateCode
    zip_code: str = Field(pattern=r"^[0-9]{5}(-[0-9]{4})?$")


class Education(InputModel):
    degree_type: Literal["bachelors", "masters", "other"]
    university_name: str = Field(min_length=1, max_length=200)
    specialization: str = Field(min_length=1, max_length=150)
    graduation_year: int = Field(ge=1900, le=2100)


class ConsultantInput(InputModel):
    email: EmailStr = Field(max_length=254)
    first_name: str = Field(min_length=1, max_length=100)
    middle_name: str | None = Field(None, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    primary_contact_number: str = Field(min_length=7, max_length=30)
    secondary_contact_number: str | None = Field(None, max_length=30)
    date_of_birth: date | None = None
    pay_rate: Decimal | None = Field(
        None, ge=0, max_digits=10, decimal_places=2
    )
    us_entry_date: date | None = None
    visa_expiration_date: date | None = None
    marketing_location: str | None = Field(None, max_length=60)
    residing_in_guest_house: bool = False
    guest_house_move_in_date: date | None = None
    current_address: Address | None = None
    preferred_states: list[StateCode] = Field(default_factory=list, max_length=56)
    open_to_relocate: bool = False
    education: list[Education] = Field(default_factory=list, max_length=15)
    current_dl_state: StateCode | None = None
    skill_id: LookupId
    work_authorization_id: LookupId | None = None
    priority: Literal["Low", "Normal", "High"] = "Normal"

    @model_validator(mode="after")
    def validate_profile(self):
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValueError("Date of birth cannot be in the future")

        if self.residing_in_guest_house and not self.guest_house_move_in_date:
            raise ValueError("Guest house move-in date is required")

        if not self.residing_in_guest_house and self.guest_house_move_in_date:
            raise ValueError("Clear the move-in date when setting guest house to false")

        return self



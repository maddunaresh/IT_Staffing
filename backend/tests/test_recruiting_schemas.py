from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.modules.recruiting.schemas import ConsultantInput


@pytest.fixture
def consultant_data():
    """Return fresh sample data for each test."""
    return {
        "email": "consultant@example.org",
        "first_name": "Test",
        "last_name": "Consultant",
        "primary_contact_number": "+1 202 555 0147",
        "skill_id": 1,
        "work_authorization_id": 1,
        "preferred_states": ["VA", "TX"],
        "current_dl_state": "WI",
    }


def test_valid_consultant_is_accepted(consultant_data):
    consultant = ConsultantInput.model_validate(consultant_data)

    assert consultant.first_name == "Test"
    assert consultant.skill_id == 1
    assert consultant.preferred_states == ["VA", "TX"]


def test_invalid_email_is_rejected(consultant_data):
    consultant_data["email"] = "invalid-email"

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert error.value.errors()[0]["loc"] == ("email",)


@pytest.mark.parametrize("skill_id", [0, -1, "1", [1]])
def test_invalid_skill_id_is_rejected(consultant_data, skill_id):
    consultant_data["skill_id"] = skill_id

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert error.value.errors()[0]["loc"] == ("skill_id",)


def test_invalid_preferred_state_is_rejected(consultant_data):
    consultant_data["preferred_states"] = ["AF"]

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert error.value.errors()[0]["loc"] == ("preferred_states", 0)


def test_lowercase_state_is_converted_to_uppercase(consultant_data):
    consultant_data["preferred_states"] = ["va", "tx"]

    consultant = ConsultantInput.model_validate(consultant_data)

    assert consultant.preferred_states == ["VA", "TX"]


def test_future_date_of_birth_is_rejected(consultant_data):
    consultant_data["date_of_birth"] = (
        date.today() + timedelta(days=1)
    ).isoformat()

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert "Date of birth cannot be in the future" in str(error.value)


def test_guest_house_requires_move_in_date(consultant_data):
    consultant_data["residing_in_guest_house"] = True

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert "Guest house move-in date is required" in str(error.value)


def test_guest_house_with_move_in_date_is_accepted(consultant_data):
    consultant_data["residing_in_guest_house"] = True
    consultant_data["guest_house_move_in_date"] = "2025-10-13"

    consultant = ConsultantInput.model_validate(consultant_data)

    assert consultant.guest_house_move_in_date == date(2025, 10, 13)


def test_bachelors_and_masters_are_accepted(consultant_data):
    consultant_data["education"] = [
        {
            "degree_type": "bachelors",
            "university_name": "Sample University",
            "specialization": "Computer Science",
            "graduation_year": 2018,
        },
        {
            "degree_type": "masters",
            "university_name": "Sample Graduate University",
            "specialization": "Information Systems",
            "graduation_year": 2021,
        },
    ]

    consultant = ConsultantInput.model_validate(consultant_data)

    assert len(consultant.education) == 2
    assert consultant.education[1].degree_type == "masters"


def test_negative_pay_rate_is_rejected(consultant_data):
    consultant_data["pay_rate"] = -10

    with pytest.raises(ValidationError) as error:
        ConsultantInput.model_validate(consultant_data)

    assert error.value.errors()[0]["loc"] == ("pay_rate",)
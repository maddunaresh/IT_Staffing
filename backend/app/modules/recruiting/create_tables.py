from app.db.session import engine
from app.modules.recruiting.models import (
    Consultant,
    ConsultantDocument,
    RecruitingBase,
)


if __name__ == "__main__":
    RecruitingBase.metadata.create_all(
        bind=engine,
        tables=[Consultant.__table__, ConsultantDocument.__table__],
    )
    print("Recruiting tables are ready.")
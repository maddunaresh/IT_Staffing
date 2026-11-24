from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import engine
from app.modules.lookups.models import LookupBase, WorkAuthorization


INITIAL_OPTIONS = ("OPT EAD", "STEM OPT", "H4 EAD", "GC", "USC", "H1B", "Other")


def main():
    LookupBase.metadata.create_all(bind=engine)

    with Session(engine) as db, db.begin():
        existing_keys = set(db.scalars(select(WorkAuthorization.name_key)))

        for name in INITIAL_OPTIONS:
            key = name.casefold()
            if key not in existing_keys:
                db.add(WorkAuthorization(name=name, name_key=key))

    print("Shared lookup tables are ready.")


if __name__ == "__main__":
    main()
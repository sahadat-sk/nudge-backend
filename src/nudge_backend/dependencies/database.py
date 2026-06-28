from collections.abc import Generator

from nudge_backend.core.database import SessionLocal


def get_db() -> Generator:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

# Data migration commands

poetry run alembic revision --autogenerate -m "add contact activities"
poetry run alembic upgrade head

## for running the app

poetry run uvicorn nudge_backend.main:app --reload

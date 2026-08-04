# Data migration commands

poetry run alembic revision --autogenerate -m "add contact activities"
poetry run alembic upgrade head

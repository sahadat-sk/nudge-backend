from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from nudge_backend.dependencies.database import get_db
from nudge_backend.repositories.contact_repository import ContactRepository
from nudge_backend.schemas.contact import ContactCreate, ContactListResponse, ContactResponse
from nudge_backend.services.contact_service import ContactService


router = APIRouter()


@router.get("/contacts", response_model=ContactListResponse)
def get_contacts(
    search: str | None = None,
    status: str | None = None,
    sort: str = "name",
    order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
        db: Session = Depends(get_db)):
    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.list()


@router.post("/contacts", response_model=ContactResponse)
def create_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.create(payload)

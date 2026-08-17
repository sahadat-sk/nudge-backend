from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from nudge_backend.auth.dependencies import CurrentUser, get_current_user
from nudge_backend.dependencies.database import get_db
from nudge_backend.repositories.contact_repository import ContactRepository
from nudge_backend.schemas.contact import ContactCreate, ContactListResponse, ContactResponse, ContactUpdate
from nudge_backend.services.contact_service import ContactService


router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/contacts", response_model=ContactListResponse)
def get_contacts(
        search: str | None = None,
        status: str | None = None,
        source: str | None = None,
        due: str | None = None,
        sort: str = "next_followup",
        order: str = "desc",
        page: int = Query(1, ge=1),
        page_size: int = Query(25, ge=1, le=100),
        db: Session = Depends(get_db)):

    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.list(search=search, status=status, source=source, due=due, sort=sort, order=order, page=page, page_size=page_size)


@router.get("/contacts/{id}", response_model=ContactResponse)
def get_contact(id: UUID, db: Session = Depends(get_db)):
    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.get(id)


@router.patch(
    "/contacts/{contact_id}",
    response_model=ContactResponse,
)
def update_activity(
    contact_id: UUID,
    body: ContactUpdate,
    db: Session = Depends(get_db),
):

    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.update(
        contact_id,
        body,
    )


@router.post("/contacts", response_model=ContactResponse)
def create_contact(payload: ContactCreate, current_user: CurrentUser, db: Session = Depends(get_db)):
    repository = ContactRepository(db)
    service = ContactService(repository)

    return service.create(current_user.id, payload)

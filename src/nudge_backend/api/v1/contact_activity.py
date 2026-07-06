from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from nudge_backend.dependencies.database import get_db
from nudge_backend.repositories.contact_activity_repository import ContactActivityRepository
from nudge_backend.schemas.contact_activity import ContactActivityCreate, ContactActivityResponse, ContactActivityUpdate
from nudge_backend.services.contact_activity_service import ContactActivityService


router = APIRouter()


@router.get(
    "/contacts/{contact_id}/activities",
    response_model=list[ContactActivityResponse],
)
def list_activities(
    contact_id: UUID,
    db: Session = Depends(get_db),
):
    repo = ContactActivityRepository(db)
    service = ContactActivityService(repo)

    return service.list(contact_id)


@router.get(
    "/contacts/{contact_id}/activities/{activity_id}",
    response_model=ContactActivityResponse,
)
def get_activity(
    contact_id: UUID,
    activity_id: UUID,
    db: Session = Depends(get_db),
):
    repo = ContactActivityRepository(db)
    service = ContactActivityService(repo)

    return service.get(contact_id, activity_id)


@router.post(
    "/contacts/{contact_id}/activities",
    response_model=ContactActivityResponse,
)
def create_activity(
    contact_id: UUID,
    body: ContactActivityCreate,
    db: Session = Depends(get_db),
):
    repo = ContactActivityRepository(db)
    service = ContactActivityService(repo)

    return service.create(contact_id, body)


@router.patch(
    "/contacts/{contact_id}/activities/{activity_id}",
    response_model=ContactActivityResponse,
)
def update_activity(
    contact_id: UUID,
    activity_id: UUID,
    body: ContactActivityUpdate,
    db: Session = Depends(get_db),
):
    repo = ContactActivityRepository(db)
    service = ContactActivityService(repo)

    return service.update(
        contact_id,
        activity_id,
        body,
    )


@router.delete(
    "/contacts/{contact_id}/activities/{activity_id}",
    status_code=204,
)
def delete_activity(
    contact_id: UUID,
    activity_id: UUID,
    db: Session = Depends(get_db),
):
    repo = ContactActivityRepository(db)
    service = ContactActivityService(repo)

    service.delete(contact_id, activity_id)

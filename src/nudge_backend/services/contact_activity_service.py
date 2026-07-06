from uuid import UUID

from fastapi import HTTPException, status

from nudge_backend.models.contact_activity import ContactActivity
from nudge_backend.repositories.contact_activity_repository import (
    ContactActivityRepository,
)
from nudge_backend.schemas.contact_activity import (
    ContactActivityCreate,
    ContactActivityUpdate,
)


class ContactActivityService:
    def __init__(self, repository: ContactActivityRepository):
        self.repository = repository

    def list(self, contact_id: UUID):
        return self.repository.list(contact_id)

    def get(
        self,
        contact_id: UUID,
        activity_id: UUID,
    ):
        activity = self.repository.get(
            contact_id=contact_id,
            activity_id=activity_id,
        )

        if activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        return activity

    def create(
        self,
        contact_id: UUID,
        body: ContactActivityCreate,
    ):
        activity = ContactActivity(
            contact_id=contact_id,
            type=body.type,
            title=body.title,
            description=body.description,
        )

        return self.repository.create(activity)

    def update(
        self,
        contact_id: UUID,
        activity_id: UUID,
        body: ContactActivityUpdate,
    ):
        activity = self.repository.update(
            contact_id=contact_id,
            activity_id=activity_id,
            data=body.model_dump(exclude_unset=True),
        )

        if activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        return activity

    def delete(
        self,
        contact_id: UUID,
        activity_id: UUID,
    ):
        activity = self.repository.get(
            contact_id=contact_id,
            activity_id=activity_id,
        )

        if activity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        self.repository.delete(activity)

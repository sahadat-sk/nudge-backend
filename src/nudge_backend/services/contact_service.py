import math
from uuid import UUID

from fastapi import HTTPException, status

from nudge_backend.models.contact import Contact
from nudge_backend.schemas.contact import ContactCreate, ContactUpdate


class ContactService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, data: ContactCreate):
        contact = Contact(**data.model_dump())
        return self.repository.create(contact)

    def update(
        self,
        contact_id: UUID,
        body: ContactUpdate,
    ):
        contact = self.repository.update(
            contact_id=contact_id,
            data=body.model_dump(exclude_unset=True),
        )

        if contact is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity not found",
            )

        return contact

    def get(self, id: UUID):
        return self.repository.get(id)

    def list(
        self,
        search: str | None,
        status: str | None,
        source: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
    ):

        items, total = self.repository.list(
            search,
            status,
            source,
            sort,
            order,
            page,
            page_size,
        )
        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": math.ceil(total/page_size)
        }

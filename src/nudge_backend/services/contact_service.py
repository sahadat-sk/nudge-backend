import math
from uuid import UUID

from nudge_backend.models.contact import Contact
from nudge_backend.schemas.contact import ContactCreate


class ContactService:
    def __init__(self, repository):
        self.repository = repository

    def create(self, data: ContactCreate):
        contact = Contact(**data.model_dump())
        return self.repository.create(contact)

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

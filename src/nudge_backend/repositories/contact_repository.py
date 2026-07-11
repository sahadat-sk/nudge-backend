from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from nudge_backend.models.contact import Contact

SORT_FIELDS = {
    "name": Contact.name,
    "status": Contact.status,
    "source": Contact.source,
    "next_followup": Contact.next_followup,
    "last_contacted": Contact.last_contacted,
}


class ContactRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, contact: Contact):
        self.db.add(contact)
        self.db.commit()
        self.db.refresh(contact)
        return contact

    def get(self, id: UUID):
        contact = self.db.get(Contact, id)
        return contact

    def update(
        self,
        contact_id: UUID,
        data: dict,
    ) -> Contact | None:
        stmt = (
            select(Contact)
            .where(
                Contact.id == contact_id,
            )
        )

        contact = self.db.scalar(stmt)

        if contact is None:
            return None

        for key, value in data.items():
            setattr(contact, key, value)

        self.db.commit()
        self.db.refresh(contact)

        return contact

    def list(
        self,
        search: str | None,
        status: str | None,
        source: str | None, sort: str,
        order: str,
        page: int,
        page_size: int,
    ):
        query = select(Contact)

        if search:
            query = query.where(
                or_(
                    Contact.name.ilike(f"%{search}%"),
                    Contact.name.op("%")(search),
                )
            )
        if status:
            query = query.where(
                Contact.status == status
            )

        if source:
            query = query.where(
                Contact.source == source
            )

        count_query = select(
            func.count()
        ).select_from(query.subquery())

        total = self.db.scalar(count_query)

        column = SORT_FIELDS.get(
            sort,
            Contact.name,
        )

        if order == "desc":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

        query = query.offset(
            (page - 1) * page_size
        ).limit(page_size)

        items = self.db.scalars(query).all()

        return items, total

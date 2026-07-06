from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from nudge_backend.models.contact_activity import ContactActivity


class ContactActivityRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, activity: ContactActivity):
        self.db.add(activity)
        self.db.commit()
        self.db.refresh(activity)

        return activity

    def get(
        self,
        contact_id: UUID,
        activity_id: UUID,
    ):
        stmt = (
            select(ContactActivity)
            .where(
                ContactActivity.id == activity_id,
                ContactActivity.contact_id == contact_id,
            )
        )

        return self.db.scalar(stmt)

    def list(self, contact_id: UUID):
        stmt = (
            select(ContactActivity)
            .where(ContactActivity.contact_id == contact_id)
            .order_by(ContactActivity.created_at.desc())
        )

        return self.db.scalars(stmt).all()

    def update(
        self,
        contact_id: UUID,
        activity_id: UUID,
        data: dict,
    ) -> ContactActivity | None:
        stmt = (
            select(ContactActivity)
            .where(
                ContactActivity.id == activity_id,
                ContactActivity.contact_id == contact_id,
            )
        )

        activity = self.db.scalar(stmt)

        if activity is None:
            return None

        for key, value in data.items():
            setattr(activity, key, value)

        self.db.commit()
        self.db.refresh(activity)

        return activity

    def delete(self, activity: ContactActivity):
        self.db.delete(activity)
        self.db.commit()

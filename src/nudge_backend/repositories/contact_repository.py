from enum import Enum
from typing import Callable
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_, func, or_, select
from sqlalchemy.sql.elements import ColumnElement

from nudge_backend.models.contact import Contact

SORT_FIELDS = {
    "name": Contact.name,
    "status": Contact.status,
    "source": Contact.source,
    "next_followup": Contact.next_followup,
    "last_contacted": Contact.last_contacted,
}


class DueFilter(str, Enum):
    ALL = "all"
    OVERDUE = "overdue"
    DUE_TODAY = "due_today"
    DUE_THIS_WEEK = "due_this_week"


def _due_filter_all(now: datetime) -> ColumnElement | None:
    return None


def _due_filter_overdue(now: datetime) -> ColumnElement:
    today = now.date()

    return and_(
        Contact.status.not_in(["Won", "Lost"]),
        Contact.next_followup.is_not(None),
        Contact.next_followup < today,
    )


def _due_filter_due_today(now: datetime) -> ColumnElement:
    today = now.date()

    return and_(

        Contact.status.not_in(["Won", "Lost"]),
        Contact.next_followup.is_not(None),
        Contact.next_followup == today,
    )


def _due_filter_due_this_week(now: datetime) -> ColumnElement:
    today = now.date()
    end_of_window = today + timedelta(days=7)

    return and_(

        Contact.status.not_in(["Won", "Lost"]),
        Contact.next_followup.is_not(None),
        Contact.next_followup >= today,
        Contact.next_followup < end_of_window,
    )


DUE_FILTERS: dict[str, Callable[[datetime], ColumnElement | None]] = {
    DueFilter.ALL: _due_filter_all,
    DueFilter.OVERDUE: _due_filter_overdue,
    DueFilter.DUE_TODAY: _due_filter_due_today,
    DueFilter.DUE_THIS_WEEK: _due_filter_due_this_week,
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
        source: str | None,
        due: str | None,
        sort: str,
        order: str,
        page: int,
        page_size: int,
        *,
        now: datetime | None = None,  # inject for deterministic tests
    ):
        now = now or datetime.now(timezone.utc)

        query = select(Contact)

        if search:
            query = query.where(
                or_(
                    Contact.name.ilike(f"%{search}%"),
                    Contact.name.op("%")(search),
                )
            )
        if status:
            query = query.where(Contact.status == status)
        if source:
            query = query.where(Contact.source == source)

        if due:
            builder = DUE_FILTERS.get(due)
            if builder is None:
                raise ValueError(f"Unknown due filter: {due!r}")
            clause = builder(now)
            if clause is not None:
                query = query.where(clause)

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query)

        column = SORT_FIELDS.get(sort, Contact.name)
        query = query.order_by(column.desc() if order ==
                               "desc" else column.asc())

        query = query.offset((page - 1) * page_size).limit(page_size)

        items = self.db.scalars(query).all()

        return items, total

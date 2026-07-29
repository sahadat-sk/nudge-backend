
from datetime import datetime, timezone
import uuid

from sqlalchemy import UUID, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from nudge_backend.models.base import Base

from enum import Enum as PyEnum

from sqlalchemy import Enum


class ActivityType(str, PyEnum):
    NOTE = "note"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    WHATSAPP = "whatsapp"
    STATUS_CHANGED = "status_changed"
    FOLLOW_UP = "follow_up"


class ContactActivity(Base):
    __tablename__ = "contact_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    contact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contacts.id", ondelete="CASCADE"),
        index=True,
    )

    type: Mapped[ActivityType] = mapped_column(
        Enum(ActivityType),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(200))

    description: Mapped[str] = mapped_column(Text())

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    contact = relationship("Contact", back_populates="activities")

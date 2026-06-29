from datetime import date
import uuid

from sqlalchemy import UUID, Date, String, null
from sqlalchemy.orm import Mapped, mapped_column

from nudge_backend.models.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    last_contacted: Mapped[date] = mapped_column(Date(), index=True)

    next_followup: Mapped[date] = mapped_column(Date(), index=True)

    source: Mapped[str] = mapped_column(String(100), index=True)

    status: Mapped[str] = mapped_column(String(100), index=True)

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from nudge_backend.models.contact_activity import ActivityType


class ContactActivityCreate(BaseModel):
    type: ActivityType
    title: str
    description: str


class ContactActivityUpdate(BaseModel):
    type: ActivityType | None = None
    title: str | None = None
    description: str | None = None


class ContactActivityResponse(BaseModel):
    id: UUID
    contact_id: UUID

    type: ActivityType

    title: str
    description: str

    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

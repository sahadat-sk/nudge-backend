from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ContactCreate(BaseModel):
    name: str
    last_contacted: date
    next_followup: date
    source: str
    status: str
    contact_details: str


class ContactUpdate(BaseModel):
    name: str | None = None
    last_contacted: date | None = None
    next_followup: date | None = None
    source: str | None = None
    status: str | None = None


class ContactResponse(BaseModel):
    id: UUID
    name: str
    last_contacted: date
    next_followup: date
    source: str
    status: str
    contact_details: str

    model_config = {
        "from_attributes": True
    }


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    pages: int

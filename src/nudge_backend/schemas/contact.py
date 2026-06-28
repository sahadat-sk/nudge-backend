from datetime import date
from uuid import UUID

from pydantic import BaseModel


class ContactCreate(BaseModel):
    name: str
    last_contacted: date
    next_followup: date
    source: str
    status: str


class ContactResponse(BaseModel):
    id: UUID
    name: str
    last_contacted: date
    next_followup: date
    source: str
    status: str

    model_config = {
        "from_attributes": True
    }


class ContactListResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    page_size: int
    pages: int

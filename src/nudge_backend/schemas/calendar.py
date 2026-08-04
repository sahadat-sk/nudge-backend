from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class EventDateTime(BaseModel):
    """
    Mirrors Google's EventDateTime resource. Exactly one of date/date_time
    should be set: `date` for all-day events ("2026-08-02"), `date_time`
    for timed events. Google requires `time_zone` when `date_time` is a
    naive (no offset) timestamp.
    """

    model_config = ConfigDict(populate_by_name=True)

    date_time: datetime | None = Field(default=None, alias="dateTime")
    date: str | None = None
    time_zone: str | None = Field(default=None, alias="timeZone")


class EventCreate(BaseModel):
    summary: str
    description: str | None = None
    location: str | None = None
    start: EventDateTime
    end: EventDateTime
    attendee_emails: list[EmailStr] = Field(default_factory=list)
    calendar_id: str = "primary"


class EventUpdate(BaseModel):
    """All fields optional — only provided fields are sent as a PATCH."""

    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: EventDateTime | None = None
    end: EventDateTime | None = None
    attendee_emails: list[EmailStr] | None = None
    calendar_id: str = "primary"


class EventMove(BaseModel):
    """Moves an event to a different calendar (Google's events.move)."""

    source_calendar_id: str = "primary"
    destination_calendar_id: str


class EventResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    start: EventDateTime
    end: EventDateTime
    html_link: str | None = Field(default=None, alias="htmlLink")
    status: str | None = None


class CalendarStatusResponse(BaseModel):
    connected: bool

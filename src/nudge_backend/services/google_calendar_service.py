import uuid
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from nudge_backend.core.config import settings
from nudge_backend.core.encryption import decrypt, encrypt
from nudge_backend.models.google_credential import GoogleCredential
from nudge_backend.repositories.google_credential_repository import GoogleCredentialRepository
from nudge_backend.schemas.calendar import EventCreate, EventMove, EventResponse, EventUpdate

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Refresh proactively rather than waiting for a 401 from Google — avoids a
# doubled round trip on almost every request near expiry.
_EXPIRY_SKEW = timedelta(seconds=60)


class GoogleCalendarService:
    """
    Per-request service for a single user's Google Calendar. Construct
    with the authenticated user; it looks up (and silently refreshes) that
    user's stored Google OAuth credential as needed.
    """

    def __init__(self, db: Session, user_id: uuid.UUID):
        self._db = db
        self._user_id = user_id
        self._credentials = GoogleCredentialRepository(db)

    # ----------------------------------------------------------------
    # Public API
    # ----------------------------------------------------------------
    async def list_events(
        self,
        *,
        calendar_id: str = "primary",
        time_min: datetime | None = None,
        time_max: datetime | None = None,
    ) -> list[EventResponse]:
        params = {"singleEvents": "true", "orderBy": "startTime"}
        if time_min:
            params["timeMin"] = time_min.isoformat()
        if time_max:
            params["timeMax"] = time_max.isoformat()

        data = await self._request(
            "GET",
            f"/calendars/{_quote(calendar_id)}/events",
            params=params,
        )
        return [EventResponse.model_validate(item) for item in data.get("items", [])]

    async def create_event(self, payload: EventCreate) -> EventResponse:
        body = _event_create_body(payload)
        print("Request body is", body)
        data = await self._request(
            "POST",
            f"/calendars/{_quote(payload.calendar_id)}/events",
            json=body,
        )
        return EventResponse.model_validate(data)

    async def update_event(self, event_id: str, payload: EventUpdate) -> EventResponse:
        body = _event_update_body(payload)
        data = await self._request(
            "PATCH",
            f"/calendars/{_quote(payload.calendar_id)}/events/{_quote(event_id)}",
            json=body,
        )
        return EventResponse.model_validate(data)

    async def delete_event(self, event_id: str, *, calendar_id: str = "primary") -> None:
        await self._request(
            "DELETE",
            f"/calendars/{_quote(calendar_id)}/events/{_quote(event_id)}",
            expect_json=False,
        )

    async def move_event(self, event_id: str, payload: EventMove) -> EventResponse:
        data = await self._request(
            "POST",
            f"/calendars/{_quote(payload.source_calendar_id)}/events/{_quote(event_id)}/move",
            params={"destination": payload.destination_calendar_id},
        )
        return EventResponse.model_validate(data)

    # ----------------------------------------------------------------
    # HTTP + token handling
    # ----------------------------------------------------------------
    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
        expect_json: bool = True,
    ) -> dict:
        access_token = await self._get_valid_access_token()

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                method,
                f"{CALENDAR_API_BASE}{path}",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
                json=json,
            )

        if response.status_code == 401:
            # Token was valid a moment ago per our records but Google
            # rejected it anyway (e.g. revoked externally). One retry
            # after a forced refresh, then give up.
            access_token = await self._refresh_access_token()
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(
                    method,
                    f"{CALENDAR_API_BASE}{path}",
                    headers={"Authorization": f"Bearer {access_token}"},
                    params=params,
                    json=json,
                )

        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Google Calendar API error ({response.status_code}): {response.text[:300]}",
            )

        if not expect_json or not response.content:
            return {}
        return response.json()

    async def _get_valid_access_token(self) -> str:
        credential = self._credentials.get_by_user_id(self._user_id)
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Calendar is not connected for this account",
            )

        if credential.expires_at - _EXPIRY_SKEW <= datetime.now(timezone.utc):
            return await self._refresh_access_token(credential)

        return decrypt(credential.access_token_encrypted)

    async def _refresh_access_token(self, credential: GoogleCredential | None = None) -> str:
        credential = credential or self._credentials.get_by_user_id(
            self._user_id)
        if credential is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google Calendar is not connected for this account",
            )

        refresh_token = decrypt(credential.refresh_token_encrypted)

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                TOKEN_ENDPOINT,
                data={
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )

        if response.status_code != 200:
            # Refresh tokens can be revoked externally (user removed app
            # access in their Google account, password change, etc).
            # Surface a clear, actionable error rather than a generic 502.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google Calendar access has expired or been revoked; please reconnect",
            )

        data = response.json()
        new_access_token = data["access_token"]
        expires_at = datetime.now(timezone.utc) + \
            timedelta(seconds=data.get("expires_in", 3600))

        credential.access_token_encrypted = encrypt(new_access_token)
        credential.expires_at = expires_at
        self._db.flush()
        self._db.commit()

        return new_access_token


def _quote(value: str) -> str:
    from urllib.parse import quote

    return quote(value, safe="")


def _event_create_body(payload: EventCreate) -> dict:
    body: dict = {
        "summary": payload.summary,
        "start": payload.start.model_dump(by_alias=True, exclude_none=True, mode='json'),
        "end": payload.end.model_dump(by_alias=True, exclude_none=True, mode='json'),
    }
    if payload.description is not None:
        body["description"] = payload.description
    if payload.location is not None:
        body["location"] = payload.location
    if payload.attendee_emails:
        body["attendees"] = [{"email": email}
                             for email in payload.attendee_emails]
    return body


def _event_update_body(payload: EventUpdate) -> dict:
    body: dict = {}
    if payload.summary is not None:
        body["summary"] = payload.summary
    if payload.description is not None:
        body["description"] = payload.description
    if payload.location is not None:
        body["location"] = payload.location
    if payload.start is not None:
        body["start"] = payload.start.model_dump(
            by_alias=True, exclude_none=True, mode='json')
    if payload.end is not None:
        body["end"] = payload.end.model_dump(
            by_alias=True, exclude_none=True, mode='json')
    if payload.attendee_emails is not None:
        body["attendees"] = [{"email": email}
                             for email in payload.attendee_emails]
    return body

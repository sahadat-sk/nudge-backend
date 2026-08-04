import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from nudge_backend.auth.dependencies import get_current_user
from nudge_backend.auth.google import oauth
from nudge_backend.core.config import settings
from nudge_backend.dependencies.database import get_db
from nudge_backend.models.user import User
from nudge_backend.repositories.google_credential_repository import GoogleCredentialRepository
from nudge_backend.schemas.calendar import (
    CalendarStatusResponse,
    EventCreate,
    EventMove,
    EventResponse,
    EventUpdate,
)
from nudge_backend.services.auth_service import AuthService
from nudge_backend.services.google_calendar_service import GoogleCalendarService

router = APIRouter(
    prefix="/calendar",
    tags=["Google Calendar"],
)

# Calendar access is requested separately from login, and only with the
# user's explicit action (clicking "Connect Google Calendar"). We ask for
# calendar.events rather than the broader `calendar` scope since we only
# need CRUD + move on events, not calendar-list management.
_CALENDAR_SCOPES = "openid email profile https://www.googleapis.com/auth/calendar.events"

_SESSION_KEY = "calendar_connect_user_id"


# ----------------------------------------------------------------------
# Connect flow (full-page browser navigations, not XHR — see frontend
# ConnectCalendarButton, which does a plain link/redirect rather than
# fetch())
# ----------------------------------------------------------------------
@router.get("/connect")
async def connect_calendar(
    request: Request,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    """
    Kicks off calendar-specific consent. Identifies the user via the same
    refresh_token cookie /auth/refresh uses — there's no Authorization
    header available here since this is a top-level navigation, not an
    XHR the frontend controls headers for.
    """
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = AuthService(db).get_user_from_refresh_token(refresh_token)

    # Stashed in the signed session cookie (SessionMiddleware) so the
    # callback knows who to attach the resulting tokens to, without
    # trusting anything client-controlled in the callback's query string.
    request.session[_SESSION_KEY] = str(user.id)

    return await oauth.google.authorize_redirect(
        request,
        settings.google_calendar_redirect_uri,
        access_type="offline",  # required to receive a refresh_token
        prompt="consent",  # forces re-consent, guaranteeing a refresh_token even on reconnect
        scope=_CALENDAR_SCOPES,
    )


@router.get("/callback")
async def calendar_callback(request: Request, db: Session = Depends(get_db)):
    user_id_str = request.session.pop(_SESSION_KEY, None)
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing calendar connect session; please retry from the app",
        )

    token = await oauth.google.authorize_access_token(request)

    expires_at = datetime.now(timezone.utc) + \
        timedelta(seconds=token.get("expires_in", 3600))

    try:
        GoogleCredentialRepository(db).upsert(
            user_id=uuid.UUID(user_id_str),
            access_token=token["access_token"],
            refresh_token=token.get("refresh_token"),
            expires_at=expires_at,
            scope=token.get("scope", ""),
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RedirectResponse(
        url=f"{settings.frontend_url}/calendar?connected=true",
        status_code=status.HTTP_302_FOUND,
    )


# ----------------------------------------------------------------------
# Status
# ----------------------------------------------------------------------
@router.get("/status", response_model=CalendarStatusResponse)
def calendar_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connected = GoogleCredentialRepository(
        db).get_by_user_id(current_user.id) is not None
    return CalendarStatusResponse(connected=connected)


# ----------------------------------------------------------------------
# Event CRUD + move (normal XHR calls, Bearer-authenticated)
# ----------------------------------------------------------------------
@router.get("/events", response_model=list[EventResponse])
async def list_events(
    calendar_id: str = "primary",
    time_min: datetime | None = None,
    time_max: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = GoogleCalendarService(db, current_user.id)
    return await service.list_events(calendar_id=calendar_id, time_min=time_min, time_max=time_max)


@router.post("/events", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = GoogleCalendarService(db, current_user.id)
    return await service.create_event(payload)


@router.patch("/events/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = GoogleCalendarService(db, current_user.id)
    return await service.update_event(event_id, payload)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    calendar_id: str = "primary",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = GoogleCalendarService(db, current_user.id)
    await service.delete_event(event_id, calendar_id=calendar_id)


@router.post("/events/{event_id}/move", response_model=EventResponse)
async def move_event(
    event_id: str,
    payload: EventMove,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = GoogleCalendarService(db, current_user.id)
    return await service.move_event(event_id, payload)

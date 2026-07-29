from sqlalchemy import select
from sqlalchemy.orm import Session

from nudge_backend.models.user import User
from nudge_backend.schemas.auth import GoogleUserInfo


class UserRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_id(self, user_id) -> User | None:
        return self._db.get(User, user_id)

    def get_by_google_id(self, google_id: str) -> User | None:
        stmt = select(User).where(User.google_id == google_id)
        return self._db.execute(stmt).scalar_one_or_none()

    def get_or_create_from_google(self, google_user: GoogleUserInfo) -> User:
        user = self.get_by_google_id(google_user.sub)

        if user is None:
            user = User(
                email=google_user.email,
                name=google_user.name,
                picture_url=google_user.picture,
                google_id=google_user.sub,
            )
            self._db.add(user)
            self._db.flush()  # populate user.id without committing yet
            return user

        # Keep profile fields fresh in case the person updated their name
        # or photo on Google since the last login.
        changed = False
        if user.name != google_user.name:
            user.name = google_user.name
            changed = True
        if user.picture_url != google_user.picture:
            user.picture_url = google_user.picture
            changed = True
        if changed:
            self._db.flush()

        return user

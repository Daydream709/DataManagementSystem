from datetime import datetime, timezone

import bcrypt
import jwt
from django.conf import settings


def hash_password(raw_password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(raw_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(raw_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(raw_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_token(user_id: str, username: str) -> str:
    now = datetime.now(tz=timezone.utc)
    payload = {
        "sub": user_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + settings.JWT_SETTINGS["EXPIRE"]).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SETTINGS["SECRET"], algorithm=settings.JWT_SETTINGS["ALGORITHM"])


def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SETTINGS["SECRET"],
        algorithms=[settings.JWT_SETTINGS["ALGORITHM"]],
    )

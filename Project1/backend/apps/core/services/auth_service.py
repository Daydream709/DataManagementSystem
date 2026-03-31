from datetime import datetime, timezone

from pymongo.errors import DuplicateKeyError
from rest_framework.exceptions import AuthenticationFailed, ValidationError

from ..mongodb import get_collection
from ..utils.security import create_token, hash_password, verify_password


def register_user(username: str, password: str) -> dict:
    users = get_collection("users")
    now = datetime.now(tz=timezone.utc)

    payload = {
        "username": username,
        "password_hash": hash_password(password),
        "created_at": now,
    }

    try:
        result = users.insert_one(payload)
    except DuplicateKeyError as exc:
        raise ValidationError({"username": "用户名已存在"}) from exc

    token = create_token(str(result.inserted_id), username)
    return {
        "id": str(result.inserted_id),
        "username": username,
        "created_at": now.isoformat(),
        "token": token,
    }


def login_user(username: str, password: str) -> dict:
    users = get_collection("users")
    user = users.find_one({"username": username})
    if not user or not verify_password(password, user["password_hash"]):
        raise AuthenticationFailed("用户名或密码错误")

    token = create_token(str(user["_id"]), username)
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "created_at": user["created_at"].isoformat(),
        "token": token,
    }

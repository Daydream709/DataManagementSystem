from dataclasses import dataclass

from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed

from .mongodb import get_collection
from .utils.helpers import to_object_id
from .utils.security import decode_token


@dataclass
class MongoUser:
    id: str
    username: str

    @property
    def is_authenticated(self) -> bool:
        return True


class MongoJWTAuthentication(authentication.BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return None

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0] != self.keyword:
            raise AuthenticationFailed("Authorization 头格式错误")

        token = parts[1]
        try:
            payload = decode_token(token)
        except Exception as exc:
            raise AuthenticationFailed("Token 无效或已过期") from exc

        user_id = payload.get("sub")
        username = payload.get("username")
        if not user_id or not username:
            raise AuthenticationFailed("Token 载荷不完整")

        try:
            user_oid = to_object_id(user_id, "user_id")
        except Exception as exc:
            raise AuthenticationFailed("Token 用户标识无效") from exc

        users = get_collection("users")
        user_doc = users.find_one({"_id": user_oid, "username": username})
        if not user_doc:
            raise AuthenticationFailed("用户不存在或已失效")

        return MongoUser(id=str(user_doc["_id"]), username=user_doc["username"]), token

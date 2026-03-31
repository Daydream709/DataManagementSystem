from datetime import datetime
from typing import Any

from bson import ObjectId
from rest_framework.exceptions import ValidationError


def to_object_id(value: str, field_name: str = "id") -> ObjectId:
    try:
        return ObjectId(value)
    except Exception as exc:
        raise ValidationError({field_name: "无效的ID格式"}) from exc


def to_iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.isoformat()


def serialize_doc(doc: dict[str, Any]) -> dict[str, Any]:
    data = {}
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            data[key] = str(value)
        elif isinstance(value, datetime):
            data[key] = value.isoformat()
        elif isinstance(value, list):
            data[key] = [
                (
                    serialize_doc(item)
                    if isinstance(item, dict)
                    else str(item) if isinstance(item, ObjectId) else item
                )
                for item in value
            ]
        elif isinstance(value, dict):
            data[key] = serialize_doc(value)
        else:
            data[key] = value
    return data

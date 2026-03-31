import logging

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        logger.exception(
            "Unhandled exception in API view: %s", context.get("view") if isinstance(context, dict) else None
        )
        message = str(exc) if settings.DEBUG else "服务器内部错误"
        return Response(
            {"code": 1, "message": message, "data": None},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = "请求失败"
    if isinstance(response.data, dict):
        detail = response.data.get("detail")
        if detail:
            message = str(detail)
        else:
            message = str(response.data)
    elif response.data:
        message = str(response.data)

    return Response({"code": 1, "message": message, "data": response.data}, status=response.status_code)

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from rest_framework.exceptions import ValidationError, PermissionDenied

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, Http404):
        return Response({"error": "Ресурс не найден"}, status=status.HTTP_404_NOT_FOUND)

    if isinstance(exc, ValidationError):
        return Response({"error": "Данные некорректны", "details": response.data},
                        status=status.HTTP_400_BAD_REQUEST)

    if isinstance(exc, PermissionDenied):
        return Response({"error": "Доступ запрещён"}, status=status.HTTP_403_FORBIDDEN)

    return response

from django.http import JsonResponse, Http404
from django.core.exceptions import (
    ValidationError,
    ObjectDoesNotExist,
    PermissionDenied,
)
from django.db import IntegrityError, DatabaseError
from rest_framework.exceptions import APIException
import logging
import traceback

logger = logging.getLogger(__name__)


# Only requests under this prefix get JSON error responses.
# Everything else (admin, portal, reports, and any random browser URL)
# falls through to Django's default HTML error handling — which uses
# templates/404.html, templates/500.html, etc.
API_PATH_PREFIX = "/api/"


class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info or ""

        # Non-API paths: let Django handle them (HTML error pages).
        if not path.startswith(API_PATH_PREFIX):
            return self.get_response(request)

        try:
            return self.get_response(request)

        except Http404 as e:
            return JsonResponse(
                {"error": "Page Not Found", "detail": str(e) or f"Not found: {path}"},
                status=404,
            )
        except ValidationError as e:
            return JsonResponse(
                {
                    "error": "Validation Error",
                    "detail": (
                        e.message_dict if hasattr(e, "message_dict") else e.messages
                    ),
                },
                status=400,
            )
        except ObjectDoesNotExist as e:
            return JsonResponse(
                {"error": "Not Found", "detail": str(e)},
                status=404,
            )
        except PermissionDenied as e:
            return JsonResponse(
                {"error": "Permission Denied", "detail": str(e)},
                status=403,
            )
        except IntegrityError as e:
            return JsonResponse(
                {"error": "Integrity Error", "detail": str(e)},
                status=400,
            )
        except DatabaseError as e:
            return JsonResponse(
                {"error": "Database Error", "detail": str(e)},
                status=500,
            )
        except APIException as e:
            return JsonResponse(
                {"error": "API Error", "detail": str(e.detail)},
                status=e.status_code,
            )
        except Exception as e:
            logger.error("Unhandled exception: %s", traceback.format_exc())
            return JsonResponse(
                {"error": "Internal Server Error", "detail": str(e)},
                status=500,
            )
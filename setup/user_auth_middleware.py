from typing import Any
from django.conf import settings
from django.http import JsonResponse
from rest_framework.exceptions import NotAuthenticated

from .helpers import get_token_info


class UserAuthMiddelware:
    """Middleware for adding view based jwt checks on keycloak_roles attribute on
    class based views"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request) -> Any:
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(view_func, "cls") or not hasattr(
            view_func.cls, "keycloak_roles"
        ):
            return

        if "HTTP_AUTHORIZATION" not in request.META:
            return JsonResponse(
                {"detail": NotAuthenticated.default_detail},
                status=NotAuthenticated.status_code,
            )

        view_func.cls.access_token = request.META["HTTP_AUTHORIZATION"].split(
            "Bearer "
        )[-1]
        view_func.cls.access_token_info = get_token_info(view_func.cls.access_token)

        # empty tokens are expired
        if not view_func.cls.access_token_info:
            return JsonResponse(
                {"detail": "Token expired"},
                status=NotAuthenticated.status_code,
            )

        # bail if not all personal roles are in class attribute keycloak_roles for
        # requested method
        if hasattr(view_func.cls, "keycloak_roles") and (
            request.method not in view_func.cls.keycloak_roles.keys()
            or not all(
                i
                in view_func.cls.access_token_info.get("resource_access", {})
                .get(settings.KEYCLOAK_CLIENT_ID, {})
                .get("roles", [])
                for i in view_func.cls.keycloak_roles.get(request.method, [])
            )
        ):
            return JsonResponse(
                {"detail": "You do not have the right role(s) for this view"},
                status=NotAuthenticated.status_code,
            )

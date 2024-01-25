from typing import Any
from django.conf import settings
from django.http import HttpRequest
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from .helpers import UserAuthMixin


class UserAuthMiddelware(UserAuthMixin):
    """Middleware for adding view based jwt checks on keycloak_roles attribute on
    class based views"""

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__()

    def __call__(self, request) -> Any:
        return self.get_response(request)

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        if not hasattr(view_func, "cls") or not hasattr(
            view_func.cls, "keycloak_roles"
        ):
            return

        if "HTTP_AUTHORIZATION" not in request.META:
            raise NotAuthenticated()

        self.access_token = request.META["HTTP_AUTHORIZATION"].split("Bearer ")[-1]

        # empty tokens are expired
        if not self.access_token_info:
            raise NotAuthenticated(detail="Token expired")

        # bail if not all personal roles are in class attribute keycloak_roles for
        # requested method
        if hasattr(view_func.cls, "keycloak_roles") and (
            request.method not in view_func.cls.keycloak_roles.keys()
            or not all(
                role in self.roles
                for role in view_func.cls.keycloak_roles.get(request.method, [])
            )
            or settings.KEYCLOAK_ROLE_IS_ACTIVE not in self.roles
        ):
            raise PermissionDenied(
                detail="You do not have the right role(s) for this view"
            )

from decouple import config
from jose import JWTError
import json
import jwt
from keycloak import KeycloakOpenID, exceptions, KeycloakPostError
import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class KeycloakAuthRolesMixin:
    def dispatch(self, request, *args, **kwargs):
        # Checks if authentication token in the http request header
        if "HTTP_AUTHORIZATION" not in request.META:
            return JsonResponse(
                {"detail": NotAuthenticated.default_detail},
                status=NotAuthenticated.status_code,
            )

        self.access_token = request.META["HTTP_AUTHORIZATION"].split("Bearer ")[-1]
        self.access_token_info = get_token_info(self.access_token)

        # empty tokens are expired
        if not self.access_token_info:
            return JsonResponse(
                {"detail": "Token expired"},
                status=NotAuthenticated.status_code,
            )

        # bail if not all personal roles are in class attribute keycloak_roles for
        # requested method
        if hasattr(self, "keycloak_roles") and not all(
            i
            in self.access_token_info.get("resource_access", {})
            .get(settings.KEYCLOAK_CLIENT_ID, {})
            .get("roles", [])
            for i in self.keycloak_roles.get(request.method, [])
        ):
            return JsonResponse(
                {"detail": "You do not have the right role(s) for this view"},
                status=NotAuthenticated.status_code,
            )
        return super().dispatch(request, *args, **kwargs)


class Login(APIView):
    """Returns keycloak token at successful login"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.keycloak_client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM_NAME,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
        )

    def post(self, request, *args, **kwargs) -> HttpResponse:
        try:
            new_token = self.keycloak_client.token(
                username=request.data.get("username"),
                password=request.data.get("password"),
            )
            access_token_info = get_token_info(new_token.get("access_token", ""))

            # check if "is_active" role is assigned to user
            if settings.KEYCLOAK_ROLE_IS_ACTIVE not in access_token_info.get(
                "resource_access", {}
            ).get(config("KEYCLOAK_CLIENT_ID"), {}).get("roles", []):
                return JsonResponse(
                    {"detail": "User account is inactive"},
                    status=NotAuthenticated.status_code,
                )

            return Response(data=new_token | access_token_info)
        except exceptions.KeycloakAuthenticationError as e:
            return Response(
                data=json.loads(e.error_message.decode()), status=e.response_code
            )


class Refresh(APIView):
    """Returns a new token given refresh_token containing a new
    access_token / refresh_token based on provided"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.keycloak_client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM_NAME,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
        )

    def post(self, request, *args, **kwargs) -> HttpResponse:
        if "HTTP_AUTHORIZATION" not in request.META:
            return JsonResponse(
                {"detail": NotAuthenticated.default_detail},
                status=NotAuthenticated.status_code,
            )

        try:
            new_token = self.keycloak_client.refresh_token(
                refresh_token=request.META["HTTP_AUTHORIZATION"].split("Bearer ")[-1]
            )
            access_token_info = get_token_info(new_token.get("access_token", ""))
            return Response(data=new_token | access_token_info)
        except KeycloakPostError as e:
            return Response(
                data=json.loads(e.error_message.decode()), status=e.response_code
            )


def get_token_info(access_token: str) -> dict[str, Any]:
    """Returns a dict with varified key values of access_token

    Args:
        access_token (str)

    Returns:
        dict[str, Any]
    """

    keycloak_client = KeycloakOpenID(
        server_url=settings.KEYCLOAK_SERVER_URL,
        client_id=settings.KEYCLOAK_CLIENT_ID,
        realm_name=settings.KEYCLOAK_REALM_NAME,
        client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
    )
    if not cache.get("keycloak_public_key"):
        cache.set(
            "keycloak_public_key",
            "-----BEGIN PUBLIC KEY-----\n"
            + keycloak_client.public_key()
            + "\n-----END PUBLIC KEY-----",
        )

    try:
        cache_key = jwt.encode(
            {"token": access_token},
            settings.CACHE_SIGNATURE,
            algorithm="HS256",
        ).split(".")[-1]

        if not (token_info := cache.get(cache_key)):
            token_info = keycloak_client.decode_token(
                token=access_token,
                key=cache.get("keycloak_public_key"),
                options={
                    "verify_signature": True,
                    "verify_aud": False,
                    "verify_exp": True,
                },
            )
            cache.set(cache_key, token_info)

    except JWTError as e:
        logging.debug(msg=e)
        token_info = {}

    return token_info

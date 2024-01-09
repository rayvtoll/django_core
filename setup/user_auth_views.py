from decouple import config
import json
from keycloak import KeycloakOpenID, exceptions, KeycloakPostError
from typing import Any

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import get_token_info
from .serializers import LoginSerializer

class Login(APIView):
    """Returns keycloak token at successful login"""

    serializer_class = LoginSerializer

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.keycloak_client = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM_NAME,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
        )

    def post(self, request, *args, **kwargs) -> HttpResponse:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_token = self.keycloak_client.token(
                username=serializer.data["username"],
                password=serializer.data["password"],
                totp=serializer.data.get("otp"),
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
        except exceptions.KeycloakPostError as e:
            return Response(
                data=json.loads(e.error_message.decode()), status=e.response_code
            )


class Refresh(APIView):
    """Returns a new token given refresh_token containing a new
    access_token / refresh_token"""

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

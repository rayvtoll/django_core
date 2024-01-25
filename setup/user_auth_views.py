from decouple import config
from keycloak import KeycloakAuthenticationError, KeycloakPostError

from django.conf import settings
from django.contrib import auth
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    ParseError,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from .helpers import UserAuthMixin
from .serializers import LoginSerializer


class Login(UserAuthMixin, APIView):
    """Returns keycloak token + django session at successful login"""

    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs) -> HttpResponse:
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            new_token = self.keycloak_client.token(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
                totp=serializer.validated_data.get("totp"),
            )
            self.access_token = new_token.get("access_token", "")

            # check if "is_active" role is assigned to user

            if settings.KEYCLOAK_ROLE_IS_ACTIVE not in self.roles:
                raise NotAuthenticated(detail="User account is inactive")

            auth.login(request, self.user)

            return Response(data=new_token | self.access_token_info)
        except KeycloakAuthenticationError as e:
            raise AuthenticationFailed(detail=e)
        except Exception as e:
            raise APIException(detail=e)


class Refresh(UserAuthMixin, APIView):
    """Returns a new token given refresh_token containing a new
    access_token / refresh_token"""

    def post(self, request, *args, **kwargs) -> HttpResponse:
        if "HTTP_AUTHORIZATION" not in request.META:
            raise NotAuthenticated()

        try:
            new_token = self.keycloak_client.refresh_token(
                refresh_token=request.META["HTTP_AUTHORIZATION"].split("Bearer ")[-1]
            )
            self.access_token = new_token.get("access_token", "")
            return Response(data=new_token | self.access_token_info)
        except KeycloakPostError as e:
            raise ParseError(detail=e)
        except Exception as e:
            raise APIException(detail=e)


class Logout(UserAuthMixin, APIView):
    """Revokes access_token & refresh_token + end django session"""

    def post(self, request: HttpResponse):
        try:
            refresh_token = request.META["HTTP_AUTHORIZATION"].split("Bearer ")[-1]
            logout(request)
            self.keycloak_client.logout(refresh_token)
        except KeycloakPostError as e:
            raise ParseError(detail=e)
        except Exception as e:
            raise APIException(detail=e, code=500)

        return Response(data={"status": "logged out"})

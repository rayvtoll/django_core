from functools import cached_property
from decouple import config
import jwt
from keycloak import KeycloakOpenID
import logging
from typing import Any, List

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.cache import cache

from .models import User


class UserAuthMixin:
    """makes sure self.keycloak_client is there and adds re-occuring functionality"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.keycloak_client: KeycloakOpenID = KeycloakOpenID(
            server_url=settings.KEYCLOAK_SERVER_URL,
            client_id=settings.KEYCLOAK_CLIENT_ID,
            realm_name=settings.KEYCLOAK_REALM_NAME,
            client_secret_key=settings.KEYCLOAK_CLIENT_SECRET_KEY,
        )

    @cached_property
    def access_token_info(self) -> dict[str, Any]:
        """Returns a dict with varified key values of access_token"""

        if not cache.get("keycloak_public_key"):
            cache.set(
                "keycloak_public_key",
                "-----BEGIN PUBLIC KEY-----\n"
                + self.keycloak_client.public_key()
                + "\n-----END PUBLIC KEY-----",
            )

        try:
            cache_key = jwt.encode(
                {"token": self.access_token},
                settings.CACHE_SIGNATURE,
                algorithm="HS256",
            ).split(".")[-1]

            if not (token_info := cache.get(cache_key)):
                token_info = self.keycloak_client.decode_token(
                    token=self.access_token,
                    key=cache.get("keycloak_public_key"),
                    options={
                        "verify_signature": True,
                        "verify_aud": False,
                        "verify_exp": True,
                    },
                )
                cache.set(cache_key, token_info)

        except Exception as e:
            logging.debug(msg=e)
            token_info = {}

        return token_info

    @cached_property
    def user(self) -> User:
        """Returns django database user object and created user session"""

        user, _ = User.objects.get_or_create(
            username=self.access_token_info.get("preferred_username"),
            first_name=self.access_token_info.get("given_name"),
            last_name=self.access_token_info.get("family_name"),
        )
        user.is_staff = settings.KEYCLOAK_ROLE_ELEVATED in self.roles
        user.is_superuser = settings.KEYCLOAK_ROLE_ELEVATED in self.roles
        user_groups = set()
        for role in self.roles:
            group, _ = Group.objects.get_or_create(name=role)
            user_groups.add(group)
        user.groups.set(user_groups)
        user.save()

        return user

    @cached_property
    def roles(self) -> List[str]:
        """Returns keycloak roles in a list"""

        try:
            roles = (
                self.access_token_info.get("resource_access", {})
                .get(config("KEYCLOAK_CLIENT_ID"), {})
                .get("roles", [])
            )
        except Exception:
            roles = []
        return roles

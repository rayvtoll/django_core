from jose.exceptions import JWTError
import jwt
from keycloak import KeycloakOpenID
import logging
from typing import Any

from django.conf import settings
from django.core.cache import cache


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

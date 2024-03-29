from decouple import config


KEYCLOAK_SERVER_URL = config("KEYCLOAK_SERVER_URL")
KEYCLOAK_CLIENT_ID = config("KEYCLOAK_CLIENT_ID")
KEYCLOAK_REALM_NAME = config("KEYCLOAK_REALM_NAME")
KEYCLOAK_CLIENT_SECRET_KEY = config("KEYCLOAK_CLIEN_SECRET_KEY")
KEYCLOAK_ROLE_IS_ACTIVE = config("KEYCLOAK_ROLE_IS_ACTIVE")
KEYCLOAK_ROLE_BASIC = config("KEYCLOAK_ROLE_BASIC")
KEYCLOAK_ROLE_ELEVATED = config("KEYCLOAK_ROLE_ELEVATED")

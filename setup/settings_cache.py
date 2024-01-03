from decouple import config


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": config("CACHE_LOCATION", "/tmp/django_cache"),
        "TIMEOUT": config("CACHE_TIMEOUT", cast=int, default=300),
    }
}
CACHE_SIGNATURE = config(
    "CACHE_SIGNATURE", "ReplaceThisStringInA.envFileBecauseThisIsNotSafe"
)

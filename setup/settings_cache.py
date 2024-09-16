from decouple import config


CACHE_LOCATION = config("CACHE_LOCATION")
CACHE_TIMEOUT = config("CACHE_TIMEOUT", cast=int, default=300)
CACHE_SIGNATURE = config("CACHE_SIGNATURE")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": CACHE_LOCATION,
        "TIMEOUT": CACHE_TIMEOUT,
    }
}

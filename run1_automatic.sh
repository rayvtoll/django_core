#!/bin/sh

pip install django --break-system-packages
python3 -m venv venv
django-admin startproject project .

# project / setting files
mkdir project/settings
echo "from .settings import *
from .settings_database import *
from .settings_cache import *
from .settings_rest_framework import *
from .settings_user_auth import *
" >> project/settings/__init__.py
mv project/settings.py project/settings/
cp setup/settings_* project/settings/
cp setup/project_urls.py project/urls.py

# user_auth files
mkdir -p project/apps/user_auth
cp setup/user_auth_views.py project/apps/user_auth/views.py
cp setup/user_auth_urls.py project/apps/user_auth/urls.py
cp setup/user_auth_admin.py project/apps/user_auth/admin.py
cp setup/user_auth_middleware.py project/apps/user_auth/middleware.py
cp setup/user_auth_helpers.py project/apps/user_auth/helpers.py
cp setup/user_auth_serializers.py project/apps/user_auth/serializers.py

# remove database lines from settings
sed -i "73d;74d;75d;76d;77d;78d;79d;80d;81d;82d;83d" project/settings/settings.py

# replace lines in settings
sed -i '1s/^/from decouple import config, Csv\n/' project/settings/settings.py
sed -i '/^SECRET_KEY = /c\SECRET_KEY = config("SECRET_KEY")' project/settings/settings.py
sed -i '/^BASE_DIR = /c\BASE_DIR = Path(__file__).resolve().parent.parent.parent' project/settings/settings.py
sed -i '/^DEBUG = /c\DEBUG = config("DEBUG", default=False, cast=bool)' project/settings/settings.py
sed -i '/^ALLOWED_HOSTS = /c\ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())' project/settings/settings.py

# cors in settings
echo 'CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", cast=Csv())' >> project/settings/settings.py
echo 'INSTALLED_APPS += ["corsheaders"]' >> project/settings/settings.py
sed -i "/^    'django.middleware.common.CommonMiddleware',/c\    'corsheaders.middleware.CorsMiddleware', 'django.middleware.common.CommonMiddleware'," project/settings/settings.py
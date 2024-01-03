#!/bin/sh

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

# remove database lines from settings
sed -i "73d;74d;75d;76d;77d;78d;79d;80d;81d;82d;83d" project/settings/settings.py

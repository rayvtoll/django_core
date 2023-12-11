#!/bin/sh

python3 -m venv venv
django-admin startproject project .

# setting files
mkdir project/settings
echo "from .settings import *
from .settings_database import *
from .settings_rest_framework import *" >> project/settings/__init__.py
mv project/settings.py project/settings/
cp core_parts/settings_database.py core_parts/settings_rest_framework.py project/settings/

# restframework files
mkdir -p project/apps/core
cp core_parts/urls.py project/
cp core_parts/serializers.py project/apps/core/
cp core_parts/views.py project/apps/core/
sed -i '34i \    \"rest_framework",' project/settings/settings.py

# remove database lines from settings
sed -i "73d;74d;75d;76d;77d;78d;79d;80d;81d;82d;83d" project/settings/settings.py

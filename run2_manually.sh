#activate venv
source venv/bin/activate

# install requirements in venv
pip install -r requirements.txt

# add abstract user before migration
echo "from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass
" >> project/apps/user_auth/models.py

python manage.py startapp user_auth project/apps/user_auth

echo "
from .settings import INSTALLED_APPS

INSTALLED_APPS += ['project.apps.user_auth']
" >> project/settings/settings_user_auth.py


echo 'AUTH_USER_MODEL = "user_auth.USER"' >> project/settings/settings.py

python manage.py makemigrations user_auth
python manage.py migrate

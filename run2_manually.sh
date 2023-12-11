#activate venv
source venv/bin/activate

# install requirements in venv
pip install -r requirements.txt

# add abstract user before migration
echo "from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass
" >> project/apps/core/models.py

# add core app + add to settings
python manage.py startapp core project/apps/core
sed -i '34i \    \"project.apps.core",' project/settings/settings.py

# oauth
sed -i '34i \    \"oauth2_provider",' project/settings/settings.py

# database migration
echo 'AUTH_USER_MODEL = "core.USER"' >> project/settings/settings.py
python manage.py makemigrations core
python manage.py migrate
python manage.py runserver

# delete the current .git directory
# start a new git and place .git directory in current directory

# go to: https://django-oauth-toolkit.readthedocs.io/en/latest/getting_started.html
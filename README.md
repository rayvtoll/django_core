Start a new Django project with all basic settings 

    sh run1_automatic.sh

Create a .env file which is a copy of the .env.example file

    cp .env .env.example

Fill in at least the following values:

    SECRET_KEY="something"
    DEBUG=true
    ALLOWED_HOSTS="*"
    CORS_ALLOWED_ORIGINS="http://localhost"

    CACHE_TIMEOUT=300
    CACHE_SIGNATURE="something"
    CACHE_LOCATION="/tmp/django_cache"

Then:

    cat run2_manually.sh

Copy the code and paste it directly into the terminal and press Enter to run the code.

Now, you should be able to run the project:

    python3 manage.py runserver

If the sh scripts fail for some reason and you want to try it again, run:

    sh delete_project.sh
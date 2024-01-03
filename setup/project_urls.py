from django.contrib import admin
from django.urls import path, include

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("user-auth/", include("project.apps.user_auth.urls")),
    path("admin/", admin.site.urls),
]

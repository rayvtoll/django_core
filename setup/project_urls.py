from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path("user-auth/", include("project.apps.user_auth.urls")),
    path("admin/", admin.site.urls),
]

from django.urls import include, path
from rest_framework import routers, serializers, viewsets

from django.conf import settings

from .views import Login, Logout, Refresh
from .models import User


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = [
            "url",
            "username",
            "first_name",
            "last_name",
            "is_active",
            "is_staff",
            "is_superuser",
        ]


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    keycloak_roles = {
        "GET": [settings.KEYCLOAK_ROLE_BASIC],
        "POST": [settings.KEYCLOAK_ROLE_ELEVATED],
        "PATCH": [settings.KEYCLOAK_ROLE_ELEVATED],
        "PUT": [settings.KEYCLOAK_ROLE_ELEVATED],
    }


router = routers.DefaultRouter()
router.register(r"users", UserViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path("login/", Login.as_view(), name="login"),
    path("logout/", Logout.as_view(), name="logout"),
    path("refresh_token/", Refresh.as_view(), name="refresh_token"),
]

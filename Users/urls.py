from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import UserViewSet, me


router = DefaultRouter()
router.register("users", UserViewSet, basename="users")

urlpatterns = router.urls + [
    path("users/me/", me, name = "me"),
]
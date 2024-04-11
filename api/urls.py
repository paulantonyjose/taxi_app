from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"user", views.UserViewSet)
router.register(r"ride", views.RideViewSet)
router.register(r"location", views.UserLocationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

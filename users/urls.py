from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import PaymentViewSet, UserProfileUpdateView

app_name = "users"

router = DefaultRouter()
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("<int:pk>/", UserProfileUpdateView.as_view(), name="user-profile"),
] + router.urls

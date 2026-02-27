from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import PaymentViewSet, RegisterView, UserProfileUpdateView, UserViewSet

app_name = "users"

router = DefaultRouter()
router.register(r"", UserViewSet, basename="users")
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    # Регистрация и авторизация - доступна всем
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Профиль пользователя c payments (для личного кабинета)
    path("profile/<int:pk>/", UserProfileUpdateView.as_view(), name="user-profile"),
] + router.urls

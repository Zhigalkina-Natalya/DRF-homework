from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from users.views import (
    CheckPaymentStatusView,
    CreateStripeSessionView,
    PaymentViewSet,
    RegisterView,
    UserProfileUpdateView,
    UserViewSet,
    payment_cancel,
    payment_success,
)

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
    path("create-stripe-session/", CreateStripeSessionView.as_view(), name="create-stripe-session"),
    path("check-payment/<str:session_id>/", CheckPaymentStatusView.as_view(), name="check-payment"),
    # страницы Stripe после оплаты
    path("success/", payment_success, name="payment-success"),
    path("cancel/", payment_cancel, name="payment-cancel"),
] + router.urls

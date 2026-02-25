from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets, permissions
from rest_framework.filters import OrderingFilter

from users.models import Payment, User
from users.serializers import PaymentSerializer, UserSerializer, UserDetailSerializer, RegisterSerializer


class RegisterView(generics.CreateAPIView):
    """
    Эндпоинт для регистрации нового пользователя.
    Доступен неавторизованным (AllowAny).
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        """Сохраняет пользователя и хеширует пароль."""
        user = serializer.save(is_active=True)
        user.set_password(user.password)
        user.save()


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD для пользователей.
    Доступ только авторизованным пользователям.
    """
    queryset = User.objects.all()
    serializer_class = UserDetailSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и обновление профиля пользователя.
    Использует UserSerializer с историей платежей.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Payment с фильтрацией и сортировкой.
    Доступ только авторизованным пользователям.
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = ["course", "lesson", "payment_method"]

    ordering_fields = ["paid_at", "amount"]

    ordering = ["-paid_at"]

    def perform_create(self, serializer):
        """Сохраняет платёж, автоматически подставляя пользователя."""
        user_id = self.request.data.get("user")
        if user_id:
            serializer.save(user_id=user_id)
        else:
            # если не передан, присвоим текущего пользователя
            serializer.save(user=self.request.user)

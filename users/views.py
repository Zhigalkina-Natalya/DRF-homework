from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import generics, permissions, viewsets
from rest_framework.filters import OrderingFilter

from users.models import Payment, User
from users.permissions import IsSelfOrReadOnly
from users.serializers import (
    PaymentSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    UserDetailSerializer,
    UserSerializer,
)


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


@extend_schema(
    summary="Просмотр и редактирование профиля пользователя",
    description=(
        "Возвращает полный профиль пользователя с платежами (если свой профиль) " "или публичный профиль (если чужой)."
    ),
    parameters=[
        OpenApiParameter(
            name="pk",
            type=int,
            location=OpenApiParameter.PATH,
            description="ID пользователя (например, /users/profile/1/)",
        )
    ],
    responses={200: UserSerializer},
)
class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    Просмотр и обновление профиля пользователя.
    Использует UserSerializer с историей платежей.
    Любой авторизованный может просматривать чужой профиль (ограниченная информация)
    Редактировать можно только свой профиль
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSelfOrReadOnly]
    lookup_field = "pk"  # для подсказки Spectacular

    def get_serializer_class(self):
        """Выбираем сериализатор в зависимости от того, чей профиль запрошен."""
        # Если профиль свой — показать полный сериализатор
        if self.get_object() == self.request.user:
            return UserSerializer
        # Если чужой — упрощённый
        return PublicUserSerializer


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

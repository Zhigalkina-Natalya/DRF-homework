from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.filters import OrderingFilter

from users.models import Payment, User
from users.serializers import PaymentSerializer, UserSerializer


class UserProfileUpdateView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PaymentViewSet(viewsets.ModelViewSet):
    """ViewSet для модели Payment с фильтрацией и сортировкой."""

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer

    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = ["course", "lesson", "payment_method", "user"]

    ordering_fields = ["paid_at", "amount"]

    ordering = ["-paid_at"]

    def perform_create(self, serializer):
        """Сохраняет платёж, подставляя пользователя, если он не указан явно."""
        user_id = self.request.data.get("user")
        if user_id:
            serializer.save(user_id=user_id)
        else:
            from users.models import User

            admin_user = User.objects.filter(is_superuser=True).first()
            serializer.save(user=admin_user)

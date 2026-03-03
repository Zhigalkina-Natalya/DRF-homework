from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course
from users.models import Payment, User
from users.permissions import IsSelfOrReadOnly
from users.serializers import (
    CreateStripeSessionSerializer,
    PaymentSerializer,
    PublicUserSerializer,
    RegisterSerializer,
    UserDetailSerializer,
    UserSerializer,
)
from users.services import create_checkout_session, create_stripe_price, create_stripe_product


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


@extend_schema(
    summary="Создание Stripe Checkout-сессии",
    description="Создаёт продукт, цену и ссылку на оплату курса в Stripe.",
    request=CreateStripeSessionSerializer,
    responses={201: dict},
)
class CreateStripeSessionView(APIView):
    """Создание Stripe-сессии для оплаты курса."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateStripeSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data["course_id"]
        success_url = serializer.validated_data["success_url"]
        cancel_url = serializer.validated_data["cancel_url"]

        # Получаем курс
        course = get_object_or_404(Course, id=course_id)

        # Для теста задаём цену
        amount = 199

        # Создаём продукт и цену в Stripe
        product = create_stripe_product(name=course.title, description=course.description)
        price = create_stripe_price(product.id, amount, "rub")

        # Создаём checkout-сессию
        metadata = {"course_id": str(course.id), "user_id": str(request.user.id)}
        session = create_checkout_session(price.id, success_url, cancel_url, metadata)

        # Получаем данные из объекта
        stripe_session_id = getattr(session, "id", None)
        checkout_url = getattr(session, "url", None)
        payment_status = getattr(session, "payment_status", "")

        # Сохраняем платёж в базе
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            amount=amount,
            payment_method="transfer",
            stripe_session_id=stripe_session_id,
            checkout_url=checkout_url,
            payment_status=payment_status,
        )

        # Возвращаем данные через getattr()
        return Response(
            {
                "message": f"Сессия оплаты создана для курса: {course.title}",
                "checkout_url": checkout_url,
                "stripe_session_id": stripe_session_id,
            },
            status=status.HTTP_201_CREATED,
        )


def payment_success(request):
    """Визуальная страница успешной оплаты."""
    return render(request, "users/success.html")


def payment_cancel(request):
    """Визуальная страница отменённой оплаты."""
    return render(request, "users/cancel.html")

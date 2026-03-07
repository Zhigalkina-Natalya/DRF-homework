from django.shortcuts import get_object_or_404, render
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, Lesson
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
from users.services import create_checkout_session, create_stripe_price, create_stripe_product, retrieve_session


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
    description="Создаёт (или использует существующий) продукт, цену и ссылку на оплату курса в Stripe.",
    request=CreateStripeSessionSerializer,
    responses={201: dict},
)
class CreateStripeSessionView(APIView):
    """Создание Stripe-сессии для оплаты курса или урока."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = CreateStripeSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = serializer.validated_data.get("course_id")
        lesson_id = serializer.validated_data.get("lesson_id")

        # Определяем объект оплаты
        if course_id:
            obj = get_object_or_404(Course, id=course_id)
        elif lesson_id:
            obj = get_object_or_404(Lesson, id=lesson_id)
        else:
            return Response({"error": "Нужно передать course_id или lesson_id"}, status=400)

        # Задаём цену курса, например:
        amount = 199

        # Создаём продукт и цену только если их нет
        if not obj.stripe_product_id:
            product = create_stripe_product(name=obj.title, description=obj.description)
            obj.stripe_product_id = product.id
            obj.save(update_fields=["stripe_product_id"])

        if not obj.stripe_price_id:
            price = create_stripe_price(obj.stripe_product_id, amount, "rub")
            obj.stripe_price_id = price.id
            obj.save(update_fields=["stripe_price_id"])

        success_url = request.build_absolute_uri("/users/success/")
        cancel_url = request.build_absolute_uri("/users/cancel/")

        metadata = {"object_type": obj.__class__.__name__, "object_id": obj.id, "user_id": request.user.id}
        session = create_checkout_session(obj.stripe_price_id, success_url, cancel_url, metadata)

        Payment.objects.create(
            user=request.user,
            course=obj if isinstance(obj, Course) else None,
            lesson=obj if isinstance(obj, Lesson) else None,
            amount=amount,
            payment_method="transfer",
            stripe_session_id=session.id,
            checkout_url=session.url,
            payment_status=session.payment_status,
        )

        return Response(
            {
                "message": f"Сессия оплаты создана для: {obj}",
                "checkout_url": session.url,
                "stripe_session_id": session.id,
            },
            status=status.HTTP_201_CREATED,
        )


def payment_success(request):
    """Визуальная страница успешной оплаты."""
    return render(request, "users/success.html")


def payment_cancel(request):
    """Визуальная страница отменённой оплаты."""
    return render(request, "users/cancel.html")


@extend_schema(
    summary="Проверка статуса оплаты по session_id",
    description="Запрашивает статус сессии в Stripe и обновляет payment_status в базе.",
    responses={200: dict, 404: dict},
)
class CheckPaymentStatusView(APIView):
    """Проверка статуса оплаты по session_id."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id):
        payment = get_object_or_404(Payment, stripe_session_id=session_id)
        session = retrieve_session(session_id)

        payment_status = session.get("payment_status") or getattr(session, "payment_status", "unknown")
        payment.payment_status = payment_status
        payment.save(update_fields=["payment_status"])

        return Response(
            {"stripe_session_id": session_id, "payment_status": payment_status},
            status=status.HTTP_200_OK,
        )

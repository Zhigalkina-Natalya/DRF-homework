from rest_framework import serializers

from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer
from users.models import Payment, User


class PaymentListSerializer(serializers.ModelSerializer):
    """Сериализатор списка платежей (для вывода в профиле пользователя)."""

    class Meta:
        model = Payment
        fields = ["id", "paid_at", "course", "lesson", "amount", "payment_method"]


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор профиля пользователя с историей платежей."""

    payments = PaymentListSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "phone", "city", "avatar", "payments"]


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["id", "email", "password", "phone", "city", "avatar"]


class UserDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и редактирования данных пользователя."""

    class Meta:
        model = User
        fields = ["id", "email", "phone", "city", "avatar", "is_active", "is_staff"]
        read_only_fields = ["is_staff", "is_active"]


class PublicUserSerializer(serializers.ModelSerializer):
    """Упрощённый сериализатор для чужого профиля."""

    class Meta:
        model = User
        fields = ["id", "email", "city", "avatar"]


class PaymentSerializer(serializers.ModelSerializer):
    """Cериализатор для модели Payment."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False, allow_null=True)
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all(), required=False, allow_null=True)

    course_detail = CourseSerializer(source="course", read_only=True)
    lesson_detail = LessonSerializer(source="lesson", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "user",
            "paid_at",
            "course",
            "course_detail",
            "lesson",
            "lesson_detail",
            "amount",
            "payment_method",
        ]


class CreateStripeSessionSerializer(serializers.Serializer):
    """Сериализатор для создания Stripe-сессии оплаты."""

    course_id = serializers.IntegerField()
    success_url = serializers.URLField()
    cancel_url = serializers.URLField()

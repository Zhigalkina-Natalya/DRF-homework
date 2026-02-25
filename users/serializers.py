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

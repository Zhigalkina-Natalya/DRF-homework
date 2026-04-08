from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from materials.models import Course, Lesson, Subscription
from materials.validators import validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    """Полный сериализатор для модели Lesson."""

    video_url = serializers.URLField(required=False, allow_null=True, validators=[validate_youtube_url])

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "preview", "video_url", "course"]


class LessonShortSerializer(serializers.ModelSerializer):
    """Сокращённый сериализатор для вывода уроков в составе курса."""

    class Meta:
        model = Lesson
        fields = ["id", "title"]


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Course. Добавляет: количество уроков в курсе, список всех связанных уроков"""

    lessons = LessonShortSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "preview", "lessons_count", "lessons", "is_subscribed"]

    @extend_schema_field(int)
    def get_lessons_count(self, obj):
        """Возвращает количество уроков, связанных с курсом."""
        return obj.lessons.count()

    @extend_schema_field(bool)
    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на курс."""
        user = self.context["request"].user
        if user.is_anonymous:
            return False
        return obj.subscriptions.filter(user=user).exists()


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для модели подписки."""

    class Meta:
        model = Subscription
        fields = ["id", "user", "course", "created_at"]
        read_only_fields = ["id", "created_at", "user"]

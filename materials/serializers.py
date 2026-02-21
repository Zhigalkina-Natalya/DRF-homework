from rest_framework import serializers

from materials.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Lesson."""

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "preview", "video_url", "course"]


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Course. Добавляет: количество уроков в курсе, список всех связанных уроков"""

    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title", "description", "preview", "lessons_count", "lessons"]

    def get_lessons_count(self, obj):
        """Возвращает количество уроков, связанных с курсом."""
        return obj.lessons.count()

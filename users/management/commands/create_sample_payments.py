from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson
from users.models import Payment

User = get_user_model()


class Command(BaseCommand):
    """Создаёт тестовые платежи для проверки."""

    help = "Создаёт примеры пользователей, курсов и платежей для тестирования."

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            email="test_user@example.com", defaults={"city": "Москва", "is_active": True}
        )

        course, _ = Course.objects.get_or_create(
            title="Django REST Framework", defaults={"description": "Учебный курс по DRF"}
        )

        lesson, _ = Lesson.objects.get_or_create(
            title="Урок 1. Введение в DRF", defaults={"course": course, "description": "Основы DRF"}
        )

        Payment.objects.get_or_create(user=user, course=course, amount=200, payment_method="transfer")
        Payment.objects.get_or_create(user=user, lesson=lesson, amount=100, payment_method="cash")

        self.stdout.write(self.style.SUCCESS("Тестовые пользователи, курсы и платежи успешно созданы!"))

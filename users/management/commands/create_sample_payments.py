from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson
from users.models import Payment

User = get_user_model()


class Command(BaseCommand):
    """Создаёт тестовые платежи для проверки."""

    help = "Создаёт примеры платежей в базе данных"

    def handle(self, *args, **options):
        user = User.objects.first()

        if not user:
            self.stdout.write(self.style.ERROR("Пользователь не найден. Создайте хотя бы одного."))
            return

        course = Course.objects.first()
        lesson = Lesson.objects.first()

        Payment.objects.create(user=user, course=course, amount=Decimal("199.00"), payment_method="transfer")
        Payment.objects.create(user=user, lesson=lesson, amount=Decimal("49.00"), payment_method="cash")

        self.stdout.write(self.style.SUCCESS("Тестовые платежи успешно созданы."))

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from materials.models import Course, Lesson


class User(AbstractUser):
    """
    Кастомный пользователь с уникальным email и доп. поля: avatar, phone, country.
    """

    username = None

    email = models.EmailField(unique=True, verbose_name="Email", help_text="Укажите почту")

    avatar = models.ImageField(
        upload_to="users/avatars/",
        verbose_name="Аватар",
        blank=True,
        null=True,
        help_text="Загрузите свой аватар",
    )
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True,
        help_text="Введите номер телефона",
    )
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name="Город")

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Payment(models.Model):
    """Модель платежей пользователей."""

    PAYMENT_METHODS = [
        ("cash", "Наличные"),
        ("transfer", "Перевод на счет"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments", verbose_name="Пользователь"
    )
    paid_at = models.DateTimeField(default=timezone.now, verbose_name="Дата оплаты")
    course = models.ForeignKey(
        Course,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
        verbose_name="Курс",
        help_text="Курс, за который произведена оплата",
    )
    lesson = models.ForeignKey(
        Lesson,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="payments",
        verbose_name="Урок",
        help_text="Урок, за который произведена оплата",
    )
    amount = models.PositiveIntegerField(verbose_name="Сумма оплаты")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name="Способ оплаты")

    def __str__(self):
        """Строковое представление платежа в админке."""
        target = self.course or self.lesson
        return f"Платёж №{self.pk} от {self.user} за {target} - {self.amount}руб."

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"
        ordering = ["-paid_at"]

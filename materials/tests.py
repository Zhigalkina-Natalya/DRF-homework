from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient, APITestCase

from materials.models import Course, Lesson, Subscription
from materials.validators import validate_youtube_url
from users.models import User


class BaseAPITestCase(APITestCase):
    """Базовый класс: создаёт пользователей, курс и уроки."""

    def setUp(self):
        self.user = User.objects.create(email="user@example.com")
        self.user.set_password("12345")
        self.user.save()

        self.moderator = User.objects.create(email="moderator@example.com")
        self.moderator.set_password("12345")
        self.moderator.save()

        group, _ = Group.objects.get_or_create(name="Модераторы")
        self.moderator.groups.add(group)

        self.client = APIClient()

        self.course = Course.objects.create(title="Тестовый курс", description="Описание", owner=self.user)
        self.lesson = Lesson.objects.create(
            title="Урок 1", description="Тестовый урок", course=self.course, owner=self.user
        )


class LessonCRUDTests(BaseAPITestCase):
    """Проверка CRUD операций для уроков."""

    def test_list_lessons_authenticated(self):
        """Авторизованный пользователь может просматривать уроки."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse("materials:lesson-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_lesson(self):
        """Пользователь может создавать уроки."""
        self.client.force_authenticate(user=self.user)
        data = {"title": "Новый урок", "description": "Описание", "course": self.course.id}
        response = self.client.post(reverse("materials:lesson-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_lesson_owner(self):
        """Владелец может редактировать свой урок."""
        self.client.force_authenticate(user=self.user)
        url = reverse("materials:lesson-detail", args=[self.lesson.id])
        response = self.client.patch(url, {"title": "Обновлённый урок"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_lesson_not_owner(self):
        """Модератор не может удалять чужие уроки."""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("materials:lesson-detail", args=[self.lesson.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_lesson_unauthorized(self):
        """Неавторизованный пользователь не может создавать урок."""
        data = {"title": "Без авторизации", "description": "Описание", "course": self.course.id}
        response = self.client.post(reverse("materials:lesson-list"), data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SubscriptionTests(BaseAPITestCase):
    """Проверка функционала подписки на курс."""

    def test_toggle_subscription_add_and_remove(self):
        """Проверяет добавление и удаление подписки."""
        self.client.force_authenticate(user=self.user)
        url = reverse("materials:subscription-toggle")

        response_add = self.client.post(url, {"course_id": self.course.id})
        self.assertEqual(response_add.status_code, status.HTTP_200_OK)
        self.assertTrue(Subscription.objects.filter(user=self.user, course=self.course).exists())

        response_remove = self.client.post(url, {"course_id": self.course.id})
        self.assertEqual(response_remove.status_code, status.HTTP_200_OK)
        self.assertFalse(Subscription.objects.filter(user=self.user, course=self.course).exists())


class ValidatorTests(TestCase):
    """Тесты для проверки валидации YouTube-ссылок."""

    def test_valid_youtube_url(self):
        """Допустимая ссылка на YouTube проходит валидацию."""
        url = "https://www.youtube.com/watch?v=123456"
        self.assertEqual(validate_youtube_url(url), url)

    def test_invalid_url(self):
        """Недопустимая ссылка вызывает ValidationError."""
        with self.assertRaises(ValidationError):
            validate_youtube_url("https://videouhuhu.com/12345")

    def test_empty_url_allowed(self):
        """Пустая ссылка разрешена."""
        self.assertIsNone(validate_youtube_url(None))

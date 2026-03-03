from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, Lesson, Subscription
from materials.paginators import CoursePagination, LessonPagination
from materials.permissions import IsModerator, IsOwner
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Course.
    Модераторы могут редактировать и просматривать, но не могут создавать или удалять курсы.
    """

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = CoursePagination

    def perform_create(self, serializer):
        """Привязывает курс к текущему пользователю, как владельцу."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Модератор и админ видят все курсы, остальные - только свои."""
        user = self.request.user
        if user.is_staff or user.groups.filter(name="Модераторы").exists():
            return Course.objects.all()
        return Course.objects.filter(owner=user)

    def get_permissions(self):
        """Настройка прав доступа для разных действий."""
        if self.action == "create":
            # создавать могут авторизованные пользователи, кроме модераторов
            self.permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        elif self.action == "destroy":
            # удалять может владелец или админ
            self.permission_classes = [permissions.IsAuthenticated, IsOwner | permissions.IsAdminUser]
        elif self.action in ["update", "partial_update", "retrieve", "list"]:
            #  редактировать и просматривать могут модераторы, владельцы и админ
            self.permission_classes = [permissions.IsAuthenticated, IsModerator | IsOwner | permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]


class LessonListCreateView(generics.ListCreateAPIView):
    """
    Список и создание уроков.
    Модераторы могут только просматривать, а создавать свои уроки могут админ и владелец.
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = LessonPagination

    def perform_create(self, serializer):
        """Привязывает урок к владельцу."""
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """Модератор и админ видят все уроки, остальные — только свои."""
        user = self.request.user
        if user.is_staff or user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        """Ограничивает создание уроков."""
        if self.request.method == "POST":
            self.permission_classes = [permissions.IsAuthenticated, ~IsModerator]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Просмотр, изменение и удаление урока. Модератор может только читать и редактировать.
    Владелец может редактировать и удалять свои. Админ может все
    """

    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        """Ограничиваем доступ к урокам владельца."""
        user = self.request.user
        if user.is_staff or user.groups.filter(name="Модераторы").exists():
            return Lesson.objects.all()
        return Lesson.objects.filter(owner=user)

    def get_permissions(self):
        """Настраивает разрешения для действий."""
        if self.request.method == "DELETE":
            # модератор не может удалять
            self.permission_classes = [permissions.IsAuthenticated, IsOwner | permissions.IsAdminUser]
        elif self.request.method in ["PUT", "PATCH", "GET"]:
            # разрешено владельцам, модераторам и админам
            self.permission_classes = [permissions.IsAuthenticated, IsModerator | IsOwner]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]


class SubscriptionToggleSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()


@extend_schema(
    request=SubscriptionToggleSerializer,
    responses={200: dict, 400: dict},
    summary="Добавление или удаление подписки",
    description="Если подписка есть — удаляется. Если нет — создаётся.",
)
class SubscriptionToggleView(APIView):
    """Добавление или удаление подписки пользователя на курс."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get("course_id")

        if not course_id:
            return Response({"error": "course_id обязателен"}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, id=course_id)
        subscription_qs = Subscription.objects.filter(user=user, course=course)

        if subscription_qs.exists():
            subscription_qs.delete()
            message = f"Подписка на курс '{course.title}' удалена."
        else:
            Subscription.objects.create(user=user, course=course)
            message = f"Подписка на курс '{course.title}' добавлена."

        return Response({"message": message}, status=status.HTTP_200_OK)

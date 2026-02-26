from rest_framework import generics, viewsets, permissions

from materials.models import Course, Lesson
from materials.permissions import IsModerator, IsOwner
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Course.
    Модераторы могут редактировать и просматривать, но не могут создавать или удалять курсы.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

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
            #  редактировать и просматривать могут модераторы и владельцы
            self.permission_classes = [permissions.IsAuthenticated, IsModerator | IsOwner]
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

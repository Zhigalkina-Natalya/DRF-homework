from rest_framework import generics, viewsets, permissions

from materials.models import Course, Lesson
from materials.permissions import IsModerator
from materials.serializers import CourseSerializer, LessonSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для модели Course.
    Модераторы могут редактировать и просматривать, но не могут создавать или удалять курсы.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        """Настройка прав доступа для разных действий."""
        if self.action in ["update", "partial_update", "retrieve", "list"]:
            self.permission_classes = [permissions.IsAuthenticated, IsModerator]
        elif self.action in ["create", "destroy"]:
            # запретить модератору, разрешить только админу
            self.permission_classes = [permissions.IsAdminUser]
        else:
            self.permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in self.permission_classes]


class LessonListCreateView(generics.ListCreateAPIView):
    """
    Список и создание уроков.
    Модераторы могут только просматривать, а создавать может только админ.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            self.permission_classes = [permissions.IsAuthenticated, IsModerator]
        elif self.request.method == "POST":
            self.permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in self.permission_classes]


class LessonRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Просмотр, изменение и удаление урока. Модератор может редактировать, но не удалять."""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method in ["GET", "PUT", "PATCH"]:
            self.permission_classes = [permissions.IsAuthenticated, IsModerator]
        elif self.request.method == "DELETE":
            self.permission_classes = [permissions.IsAdminUser]
        return [permission() for permission in self.permission_classes]

from django.urls import path
from rest_framework.routers import DefaultRouter

from materials.apps import MaterialsConfig
from materials.views import CourseViewSet, LessonListCreateView, LessonRetrieveUpdateDestroyView

app_name = MaterialsConfig.name

router = DefaultRouter()
router.register(r"courses", CourseViewSet)

urlpatterns = [
    path("lessons/", LessonListCreateView.as_view(), name="lesson-list"),
    path("lessons/<int:pk>/", LessonRetrieveUpdateDestroyView.as_view(), name="lesson-detail"),
]

urlpatterns += router.urls

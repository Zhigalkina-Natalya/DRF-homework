from django.urls import path

from users.views import UserProfileUpdateView

app_name = "users"

urlpatterns = [
    path("<int:pk>/", UserProfileUpdateView.as_view(), name="user-profile"),
]

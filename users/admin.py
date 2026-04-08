from django.contrib import admin

from materials.models import Course, Lesson
from users.models import Payment, User


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "description")
    search_fields = ("title",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "video_url")
    list_filter = ("course",)
    search_fields = ("title",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "lesson", "amount", "payment_method", "paid_at")
    list_filter = ("payment_method", "paid_at")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "phone", "city", "is_staff", "is_active")
    search_fields = ("email",)

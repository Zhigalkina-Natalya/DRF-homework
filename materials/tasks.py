import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from materials.models import Course, Subscription

logger = logging.getLogger("materials.tasks")


@shared_task
def send_course_update_email(course_id):
    """Отправляет письма подписчикам курса при обновлении."""
    try:
        course = Course.objects.get(id=course_id)

        # Проверяем время последнего уведомления
        if course.last_notification_at:
            delta = timezone.now() - course.last_notification_at

            if delta < timedelta(hours=4):
                logger.info(f"Уведомление не отправлено. " f"Курс {course.id} обновлялся менее 4 часов назад.")
                return "Слишком частое обновление"

        subscriptions = Subscription.objects.filter(course=course)

        if not subscriptions.exists():
            logger.info(f"Нет подписчиков для курса {course.id} - {course.title}")
            return "Нет подписчиков"

        for sub in subscriptions:
            try:
                send_mail(
                    subject=f"Обновление курса: {course.title}",
                    message=f'Курс "{course.title}" был обновлён.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[sub.user.email],
                    fail_silently=False,
                )

                logger.info(f"Письмо отправлено {sub.user.email} для курса {course.id}")

            except Exception as e:
                logger.error(f"Ошибка отправки письма {sub.user.email}: {e}")

        logger.info(f"Отправлено {subscriptions.count()} писем")

        # обновляем время последнего уведомления
        course.last_notification_at = timezone.now()
        course.save(update_fields=["last_notification_at"])

        return f"Отправлено {subscriptions.count()} писем"

    except Course.DoesNotExist:
        logger.error(f"Курс {course_id} не найден")

    except Exception as e:
        logger.error(f"Ошибка задачи: {e}")
        return "Ошибка выполнения задачи"

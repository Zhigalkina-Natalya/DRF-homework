import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from users.models import User

logger = logging.getLogger("users.tasks")


@shared_task
def deactivate_inactive_users():
    """
    Задача блокировки пользователей, которые не заходили более месяца.
    """
    now = timezone.now()
    inactive_threshold = now - timedelta(days=30)  # 30 дней

    # выбираем активных пользователей, не заходивших более 30 дней
    users_to_deactivate = User.objects.filter(is_active=True, last_login__lt=inactive_threshold)

    count = users_to_deactivate.count()
    for user in users_to_deactivate:
        user.is_active = False
        user.save(update_fields=["is_active"])
        logger.info(f"Пользователь {user.email} заблокирован (не заходил с {user.last_login})")

    logger.info(f"Задача deactivate_inactive_users выполнена: {count} пользователей заблокировано.")
    return f"{count} пользователей заблокировано"

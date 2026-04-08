from rest_framework import serializers


def validate_youtube_url(value):
    """Проверяет, что ссылка ведет на YouTube. Разрешены домены youtube.com."""
    if value is None or value == "":
        return value  # пустое значение разрешаем (поле необязательное)

    allowed_domains = ["youtube.com"]
    if not any(domain in value for domain in allowed_domains):
        raise serializers.ValidationError(f"Разрешены только ссылки на {', '.join(allowed_domains)}.")
    return value

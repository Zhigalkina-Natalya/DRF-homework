# Базовый образ
FROM python:3.13-slim
# отключаем создание .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# вывод логов без буфера
ENV PYTHONUNBUFFERED=1

# Рабочая папка внутри контейнера
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update \
    && apt-get install -y gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY pyproject.toml poetry.lock* .

# Устанавливаем Poetry
RUN pip install poetry

# Устанавливаем зависимости
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root

# Копируем весь проект
COPY . .

# Открываем порт Django
EXPOSE 8000

# Создаём папку для логов
RUN mkdir -p /app/logs \
    && touch /app/logs/tasks.log \
    && touch /app/logs/debug.log \
    && chmod -R 777 /app/logs

# Команда запуска Django
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]

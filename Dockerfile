# Устанавливаем базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml ./
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения внутри контейнера
COPY . /app

# Открываем порт для FastAPI
EXPOSE 8001

# Команда запуска приложения
CMD ["uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8001"]
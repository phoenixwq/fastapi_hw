## Базовый образ для сборки
FROM python:3.9.10-slim

# Указываем рабочую директорию
WORKDIR /usr/src/app

# Запрещаем Python писать файлы .pyc на диск
ENV PYTHONDONTWRITEBYTECODE 1
# Запрещает Python буферизовать stdout и stderr
ENV PYTHONUNBUFFERED 1

# Установка зависимостей проекта
COPY ./requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir

# Копируем проект
COPY . .

# Запускаем проект
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
#CMD ["python", "main.py"]

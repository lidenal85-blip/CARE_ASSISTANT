FROM python:3.13-slim

WORKDIR /app

# Зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем leviathan-core
COPY ../leviathan-core /leviathan-core
RUN pip install --no-cache-dir /leviathan-core

# Копируем проект
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Тома для данных

CMD ["python", "main.py"]

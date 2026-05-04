FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем leviathan-core из локальной папки
COPY leviathan-core /leviathan-core
RUN pip install --no-cache-dir /leviathan-core

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]

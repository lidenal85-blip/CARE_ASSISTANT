FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем leviathan-core из локальной папки
COPY leviathan-core /leviathan-core
RUN pip install --no-cache-dir /leviathan-core

COPY . .
CMD ["bash", "start_all.sh"]

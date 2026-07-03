FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Открываем порт 80, чтобы Render не ругался
EXPOSE 80

CMD ["python", "bot.py"]

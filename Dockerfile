FROM python:3.12-slim

WORKDIR /app

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodu
COPY . .

EXPOSE 8050

# Development: python ile başlat
CMD ["python", "index.py"]

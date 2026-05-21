FROM python:3.11-slim-bookworm

WORKDIR /app

# Instalar dependencias del sistema para compilar psutil en ARM (Raspberry Pi)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]

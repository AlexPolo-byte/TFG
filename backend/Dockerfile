FROM python:3.11-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --- CAMBIO AQUÍ ---
# Antes: CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
# Ahora:
CMD ["python", "app.py"]

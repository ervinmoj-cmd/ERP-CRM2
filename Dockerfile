FROM python:3.12-slim

WORKDIR /app

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el proyecto
COPY . .

# Puerto por defecto (Coolify puede usar PORT)
ENV PORT=8000
EXPOSE 8000

# Ejecutar Flask con Gunicorn
CMD ["sh", "-c", "gunicorn -w 2 -b 0.0.0.0:${PORT} wsgi:app"]

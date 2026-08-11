# Stage 1: Tailwind build
FROM node:20-slim AS tailwind
WORKDIR /app
COPY package.json package-lock.json* ./
COPY tailwind.config.js ./
COPY postcss.config.js* ./
COPY static/src ./static/src
COPY templates ./templates
COPY oferty ./oferty
RUN npm install && npm run build:css

# Stage 2: Django runtime
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=portal.settings

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsqlite3-0 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=tailwind /app/static/css ./static/css

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "portal.wsgi", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "1", \
     "--threads", "4", \
     "--preload", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]

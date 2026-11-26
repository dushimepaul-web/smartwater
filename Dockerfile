# ---------- Étape 1 : compilation des dépendances (mysqlclient a besoin d'un compilateur) ----------
FROM python:3.13-slim AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential default-libmysqlclient-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ---------- Étape 2 : image finale, légère ----------
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DEBUG=False
RUN apt-get update && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 smartwater
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

WORKDIR /app
COPY --chown=smartwater:smartwater . .
RUN chmod +x docker/entrypoint.sh \
    && DJANGO_SECRET_KEY=construction-seulement DB_ENGINE=sqlite python manage.py collectstatic --noinput \
    && chown -R smartwater:smartwater /app/staticfiles

USER smartwater
EXPOSE 8000
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]

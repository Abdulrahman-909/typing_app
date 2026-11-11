FROM python:3.12-slim
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt
COPY . .
RUN python manage.py collectstatic --noinput && useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]

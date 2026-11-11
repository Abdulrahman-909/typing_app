# Website deployment
Set a unique SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS and a real email backend. Set DJANGO_SETTINGS_MODULE=config.settings.prod. Keep .env out of Git.

For Docker set POSTGRES_PASSWORD, then:
```
docker compose build
docker compose up -d db redis
docker compose run --rm web python manage.py migrate
docker compose run --rm web python manage.py seed_demo_data
docker compose run --rm web python manage.py createsuperuser
docker compose up -d web
```
Use an HTTPS reverse proxy. Configure trusted forwarded-protocol handling only when your proxy strips client-supplied forwarded headers; the sample does not blindly trust them. For a single trusted proxy deployment set SECURE_PROXY_SSL_HEADER in prod.py appropriately to avoid redirect loops. Configure WebSocket forwarding for races. The compose web port binds to loopback.

For web without races, Gunicorn config.wsgi:application is sufficient. WhiteNoise serves collected static assets. Back up PostgreSQL independently. Run python manage.py check --deploy under production settings. The in-process login/reset limiter is a baseline; use a shared cache or edge rate limiter across workers. Use strong admin credentials and add 2FA before public administration.

No hosting or GitHub account has been connected automatically. PostgreSQL, Docker, SMTP delivery, HTTPS proxy behavior and Windows CI remain unexecuted in this environment.

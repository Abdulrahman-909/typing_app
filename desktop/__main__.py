"""Windows launcher; --smoke verifies the local server without a GUI."""

import os
import secrets
import time
import threading
import logging
import json
import argparse
from logging.handlers import RotatingFileHandler
from pathlib import Path
from filelock import FileLock, Timeout
from .paths import data_dir


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--backup")
    parser.add_argument("--restore")
    parser.add_argument("--confirm-restore", action="store_true")
    args = parser.parse_args()
    directory = data_dir()
    handler = RotatingFileHandler(directory / "desktop.log", maxBytes=1_000_000, backupCount=3)
    logging.basicConfig(handlers=[handler], level=logging.WARNING)
    lock = FileLock(directory / "app.lock")
    try:
        lock.acquire(timeout=0)
    except Timeout:
        print("The application is already running. Switch to its open window.")
        return 0
    server = None
    thread = None
    try:
        os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings.desktop"
        os.environ["DESKTOP_TOKEN"] = secrets.token_urlsafe(48)
        import django

        django.setup()
        from django.conf import settings
        from django.core.management import call_command
        from django.db import connections
        from django.db.migrations.executor import MigrationExecutor
        from .backup import backup, restore

        database = Path(settings.DATABASES["default"]["NAME"])
        if args.restore:
            connections.close_all()
            restore(database, args.restore, args.confirm_restore)
            print("Backup restored.")
            return 0
        executor = MigrationExecutor(connections["default"])
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if pending and database.exists() and database.stat().st_size:
            backup(database, directory / f"pre-migration-{time.time_ns()}.zip")
        call_command("migrate", interactive=False, verbosity=0)
        call_command("seed_demo_data", verbosity=0)
        if args.backup:
            backup(database, args.backup)
            print("Backup saved.")
            return 0
        from waitress import create_server
        from django.core.wsgi import get_wsgi_application

        server = create_server(get_wsgi_application(), host="127.0.0.1", port=0, threads=4)
        settings.DESKTOP_PORT = server.effective_port
        settings.SESSION_COOKIE_NAME = "typeatlas_desktop_" + str(server.effective_port)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        import urllib.request
        import urllib.error

        origin = f"http://127.0.0.1:{server.effective_port}"
        for attempt in range(50):
            try:
                urllib.request.urlopen(origin + "/health/", timeout=0.2)
                break
            except urllib.error.HTTPError as e:
                if e.code == 403:
                    break  # Server ready; the gate intentionally blocks unauthenticated probes.
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError("Local server did not become ready")
        if args.smoke:
            from urllib.parse import urlencode
            from http.cookiejar import CookieJar

            opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
            response = opener.open(
                origin + "/local/bootstrap/", urlencode({"token": settings.DESKTOP_TOKEN}).encode()
            )
            assert response.status == 200
            response.read()
            response.close()
            assert json.load(opener.open(origin + "/health/"))["ok"]
            print("Desktop smoke: bootstrap, home, and authenticated health passed.")
            return 0
        import webview

        # Seed the session using a header-free, POST-only token exchange from the native bridge.
        from urllib.parse import urlencode
        from http.cookiejar import CookieJar

        jar = CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
        opener.open(
            origin + "/local/bootstrap/", urlencode({"token": settings.DESKTOP_TOKEN}).encode()
        ).read()
        session_cookie = next(c for c in jar if c.name == settings.SESSION_COOKIE_NAME)
        # HTTP cookie is injected at WSGI boundary once using an unguessable launch URL,
        # removed immediately by redirect. Token is never logged and URL is one-use.
        launch = secrets.token_urlsafe(32)
        original = server.application

        def launch_app(environ, start_response):
            nonlocal launch
            if launch and environ.get("PATH_INFO") == "/launch/" + launch:
                launch = ""
                start_response(
                    "302 Found",
                    [
                        ("Location", "/"),
                        (
                            "Set-Cookie",
                            f"{session_cookie.name}={session_cookie.value}; Path=/; HttpOnly; SameSite=Strict",
                        ),
                        ("Cache-Control", "no-store"),
                    ],
                )
                return [b""]
            return original(environ, start_response)

        server.application = launch_app
        webview.create_window(
            settings.PROJECT_NAME,
            origin + "/launch/" + launch,
            width=1280,
            height=880,
            min_size=(850, 600),
        )
        webview.start(private_mode=True)
        return 0
    except Exception:
        logging.exception("Desktop startup failed")
        print(
            f"Unable to start. See {directory / 'desktop.log'}. On Windows, ensure WebView2 is installed."
        )
        if args.smoke:
            raise
        return 1
    finally:
        if server:
            server.task_dispatcher.shutdown()
            server.close()
        if thread:
            thread.join(timeout=3)
        try:
            from django.db import connections

            connections.close_all()
        except Exception:
            pass
        lock.release()


if __name__ == "__main__":
    raise SystemExit(main())

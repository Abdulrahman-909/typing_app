import os
import sys
import subprocess

args = sys.argv[1:]
port = args[args.index("--port") + 1] if "--port" in args else "4173"
os.environ["ALLOWED_HOSTS"] = "*"
raise SystemExit(
    subprocess.call([sys.executable, "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload"])
)

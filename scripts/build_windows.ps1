$ErrorActionPreference = "Stop"
python -m pip install -r requirements/desktop.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
python manage.py collectstatic --noinput
if ($LASTEXITCODE -ne 0) { throw "Static collection failed" }
python -m PyInstaller --clean --noconfirm desktop.spec
if ($LASTEXITCODE -ne 0) { throw "Build failed" }

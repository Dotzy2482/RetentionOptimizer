@echo off
echo Retention Sistemi Baslatiliyor...
start "Backend" cmd /k "cd /d %~dp0..\retention_backend && call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
timeout /t 3 /nobreak
start "Desktop" cmd /k "cd /d %~dp0..\retention_desktop && python main.py"
echo Acildi. Mobil emulator ayri olarak Android Studio'dan acilmali.
pause

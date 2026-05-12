@echo off
cd /d "%~dp0..\retention_backend"
call venv\Scripts\activate
echo Backend baslatiliyor: http://localhost:8000
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause

@echo off
echo Starting Gemini Knowledge Base App...

start cmd /k "cd backend && python -m uvicorn main:app --port 8000"
start cmd /k "cd frontend && npm run dev"

echo.
echo Application is starting!
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause

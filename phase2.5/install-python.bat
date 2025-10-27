@echo off
echo Installing Phase 2.5 Python Dependencies...
echo =========================================

echo.
echo Installing Core API dependencies...
pip install --upgrade pip
pip install livekit-api
pip install asyncio-nats-client
pip install pillow
pip install asyncpg
pip install fastapi
pip install uvicorn
pip install pydantic
pip install python-multipart
pip install python-jose
pip install passlib
pip install python-dotenv

echo.
echo Installing Desktop Agent dependencies...
pip install livekit
pip install pynput
pip install requests
pip install psutil
pip install pywin32

echo.
echo =========================================
echo Installation complete!
echo.
pause
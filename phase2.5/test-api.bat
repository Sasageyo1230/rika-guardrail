@echo off
echo Testing Rika Core API startup...
echo ==================================

cd core
echo Starting Core API on port 5317...
python -c "import sys; print('Python version:', sys.version)"
python -c "import fastapi; print('FastAPI available')"
python -c "import uvicorn; print('Uvicorn available')"

echo.
echo Starting API server...
python -m uvicorn api:app --host 0.0.0.0 --port 5317 --reload
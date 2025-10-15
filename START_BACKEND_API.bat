@echo off
REM ===============================================
REM  Start Backend API for Quote Generation
REM ===============================================
REM  This script starts the FastAPI backend server
REM  Required for quote calculations to work
REM ===============================================

echo.
echo ========================================
echo  Starting Wholesale Portal Backend API
echo ========================================
echo.
echo Backend will run on: http://localhost:8000
echo API docs available at: http://localhost:8000/docs
echo.
echo Press CTRL+C to stop the server
echo.

REM Activate virtual environment (if exists)
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Warning: Virtual environment not found
    echo Attempting to run with system Python...
)

REM Navigate to backend app directory
cd backend\app

REM Start the FastAPI server
echo.
echo Starting uvicorn server...
echo.
python -m uvicorn main:app --reload --port 8000

pause


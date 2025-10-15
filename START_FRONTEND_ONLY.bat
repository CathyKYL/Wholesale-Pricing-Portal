@echo off
echo ================================================================================
echo  BOOK PORTAL - Frontend Only Mode (Static Data Display)
echo ================================================================================
echo.
echo Starting frontend server on http://localhost:5500
echo.
echo This will display static product information from your database.
echo Quote prices are placeholders for now.
echo.
echo Press Ctrl+C to stop the server.
echo.
echo ================================================================================
echo.

cd "Front end"
python -m http.server 5500







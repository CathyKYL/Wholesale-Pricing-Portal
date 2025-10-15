@echo off
REM ===============================================
REM  Add Supabase to System PATH
REM ===============================================
REM  This script adds Supabase CLI to your PATH
REM  so you can run 'supabase' from anywhere
REM ===============================================

echo.
echo ========================================
echo  Adding Supabase to System PATH
echo ========================================
echo.

REM Define the Supabase directory
set SUPABASE_DIR=C:\VibeCode\Wholesale Pricing Portal\Supabase

echo Supabase Directory: %SUPABASE_DIR%
echo.

REM Check if directory exists
if not exist "%SUPABASE_DIR%" (
    echo ERROR: Directory does not exist!
    echo Please make sure Supabase is installed at:
    echo %SUPABASE_DIR%
    echo.
    pause
    exit /b 1
)

echo Adding to System PATH...
echo.
echo NOTE: This requires Administrator privileges
echo Please approve the UAC prompt if it appears
echo.
pause

REM Add to system PATH using PowerShell (requires admin)
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -Command \"[Environment]::SetEnvironmentVariable(''Path'', [Environment]::GetEnvironmentVariable(''Path'', ''Machine'') + '';C:\VibeCode\Wholesale Pricing Portal\Supabase'', ''Machine'')\"'"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  SUCCESS! Supabase added to PATH
    echo ========================================
    echo.
    echo IMPORTANT: Close and reopen your terminal/PowerShell
    echo for the changes to take effect.
    echo.
    echo After reopening, test with:
    echo   supabase --version
    echo.
) else (
    echo.
    echo ========================================
    echo  Failed to add to PATH
    echo ========================================
    echo.
    echo You can add it manually:
    echo 1. Open Windows Settings
    echo 2. Search for "Environment Variables"
    echo 3. Click "Edit the system environment variables"
    echo 4. Click "Environment Variables" button
    echo 5. Under "System variables", select "Path"
    echo 6. Click "Edit"
    echo 7. Click "New"
    echo 8. Add: C:\VibeCode\Wholesale Pricing Portal\Supabase
    echo 9. Click OK on all dialogs
    echo.
)

pause






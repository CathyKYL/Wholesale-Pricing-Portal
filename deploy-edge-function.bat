@echo off
REM ===============================================
REM  Deploy Supabase Edge Function
REM ===============================================
REM  Deploys the generate_quote Edge Function
REM  to Supabase with proper CORS configuration
REM ===============================================

echo.
echo ========================================
echo  Deploying Edge Function to Supabase
echo ========================================
echo.
echo Function: generate_quote
echo Location: supabase/functions/generate_quote/
echo.

REM Check if Supabase CLI is installed
where supabase >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Supabase CLI not found!
    echo.
    echo Please install it first:
    echo   npm install -g supabase
    echo.
    echo Or with Scoop:
    echo   scoop install supabase
    echo.
    pause
    exit /b 1
)

echo Step 1: Checking Supabase CLI version...
supabase --version
echo.

echo Step 2: Deploying generate_quote function...
echo.
supabase functions deploy generate_quote --project-ref mofhylcyainzwbrcmrqg

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  Deployment Successful!
    echo ========================================
    echo.
    echo Function URL:
    echo https://mofhylcyainzwbrcmrqg.supabase.co/functions/v1/generate_quote
    echo.
    echo Next steps:
    echo 1. Test your website - open Front end/index.html
    echo 2. Search for a product and click on it
    echo 3. Watch the quote calculate!
    echo.
    echo View logs:
    echo   supabase functions logs generate_quote --follow
    echo.
) else (
    echo.
    echo ========================================
    echo  Deployment Failed!
    echo ========================================
    echo.
    echo Common issues:
    echo 1. Not logged in: Run 'supabase login'
    echo 2. Project not linked: Run 'supabase link --project-ref mofhylcyainzwbrcmrqg'
    echo 3. No internet connection
    echo.
    echo Try these commands:
    echo   supabase login
    echo   supabase link --project-ref mofhylcyainzwbrcmrqg
    echo   supabase functions deploy generate_quote
    echo.
)

pause






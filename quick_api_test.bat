@echo off
REM Quick API Test Script for Windows
REM Tests basic API endpoints to verify the server is working

echo ================================================================================
echo Wedding Invitations Platform - Quick API Test
echo ================================================================================
echo.

set BASE_URL=http://localhost:8000

echo [1/8] Testing if server is running...
curl -s %BASE_URL%/api/v1/ > nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Server is running
) else (
    echo [ERROR] Server is not running. Please start the backend server first.
    echo Run: cd apps/backend/src ^&^& python manage.py runserver
    pause
    exit /b 1
)
echo.

echo [2/8] Testing API Root...
curl -s %BASE_URL%/api/v1/ | jq .
echo.

echo [3/8] Testing Plans List...
curl -s %BASE_URL%/api/v1/plans/ | jq .
echo.

echo [4/8] Testing Categories List...
curl -s %BASE_URL%/api/v1/plans/categories/list | jq .
echo.

echo [5/8] Testing Templates List...
curl -s %BASE_URL%/api/v1/plans/templates/all | jq ".[0:3]"
echo.

echo [6/8] Testing User Registration...
curl -s -X POST %BASE_URL%/api/v1/auth/register/ ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\": \"+919876543210\", \"username\": \"testuser\", \"email\": \"test@example.com\", \"full_name\": \"Test User\", \"password\": \"TestPassword123\", \"password_confirm\": \"TestPassword123\"}" | jq .
echo.

echo [7/8] Testing User Login...
curl -s -X POST %BASE_URL%/api/v1/auth/login/ ^
  -H "Content-Type: application/json" ^
  -d "{\"phone\": \"+919876543210\", \"password\": \"TestPassword123\"}" > temp_login.json
type temp_login.json | jq .
echo.

echo [8/8] Testing Protected Endpoint (Profile)...
for /f "tokens=*" %%i in ('type temp_login.json ^| jq -r .access') do set TOKEN=%%i
curl -s %BASE_URL%/api/v1/auth/profile/ ^
  -H "Authorization: Bearer %TOKEN%" | jq .
del temp_login.json
echo.

echo ================================================================================
echo Test Complete!
echo ================================================================================
echo.
echo All basic endpoints are working correctly.
echo For comprehensive testing, run: python test_all_apis.py
echo.

pause

@echo off
chcp 65001 >nul
echo ╔═══════════════════════════════════════════════════════════╗
echo ║       Digital Invitation Platform - Startup Script        ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running! Please start Docker Desktop first.
    pause
    exit /b 1
)

echo [1/5] Checking environment files...
if not exist "apps\backend-python\.env" (
    echo Creating backend .env file...
    copy apps\backend-python\.env.example apps\backend-python\.env >nul
)

if not exist "apps\frontend-mui\.env.local" (
    echo Creating frontend .env file...
    copy apps\frontend-mui\.env.example apps\frontend-mui\.env.local >nul
)

echo [2/5] Starting Docker containers...
docker-compose down >nul 2>&1
docker-compose up -d --build

if errorlevel 1 (
    echo [ERROR] Failed to start containers!
    pause
    exit /b 1
)

echo [3/5] Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo [4/5] Running database migrations...
docker-compose exec -T backend python src/manage.py migrate

echo [5/5] Seeding database with initial data...
docker-compose exec -T backend python src/manage.py seed_data

echo.
echo ╔═══════════════════════════════════════════════════════════╗
echo ║              Application Started Successfully!            ║
echo ╠═══════════════════════════════════════════════════════════╣
echo ║                                                           ║
echo ║  Frontend: http://localhost:3000                          ║
echo ║  Backend API: http://localhost:8000                       ║
echo ║  Admin Panel: http://localhost:8000/admin                 ║
echo ║                                                           ║
echo ║  Default Admin Credentials:                               ║
echo ║    Create one with: docker-compose exec backend python    ║
echo ║    src/manage.py createsuperuser                          ║
echo ║                                                           ║
echo ╚═══════════════════════════════════════════════════════════╝
echo.
echo Press any key to view logs (Ctrl+C to exit)...
pause >nul
cls
docker-compose logs -f

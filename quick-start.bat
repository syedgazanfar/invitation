@echo off
REM Wedding Invitations Platform - Quick Start Script for Windows
REM This script automates the setup and deployment process

echo =========================================
echo   Wedding Invitations Platform
echo   Quick Start Setup
echo =========================================
echo.

REM Check if Docker is installed
echo Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)
echo [OK] Docker is installed

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)
echo [OK] Docker Compose is installed
echo.

REM Stop existing containers
echo Stopping existing containers if any...
docker-compose down -v 2>nul
echo [OK] Stopped existing containers
echo.

REM Ask about cache cleanup
set /p CLEAN="Do you want to clean Docker cache? This will remove all unused images. (y/N): "
if /i "%CLEAN%"=="y" (
    echo Cleaning Docker cache...
    docker system prune -a -f
    echo [OK] Docker cache cleaned
) else (
    echo [WARNING] Skipping cache cleanup
)
echo.

REM Build containers
echo Building Docker containers this may take a few minutes...
docker-compose build --no-cache
if errorlevel 1 (
    echo [ERROR] Build failed. Check the error messages above.
    pause
    exit /b 1
)
echo [OK] Containers built successfully
echo.

REM Start containers
echo Starting containers...
docker-compose up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers. Check the error messages above.
    pause
    exit /b 1
)
echo [OK] Containers started
echo.

REM Wait for services
echo Waiting for services to be ready...
timeout /t 10 /nobreak >nul
echo [OK] Services should be ready
echo.

REM Verify setup
echo Verifying setup...
docker-compose ps
echo.

REM Check if backend is responding
echo Checking backend API...
curl -s http://localhost:9301/api/plans >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Backend might not be ready yet. Wait a few more seconds.
) else (
    echo [OK] Backend API is responding
)
echo.

REM Display access information
echo =========================================
echo   Setup Complete!
echo =========================================
echo.
echo Access your application:
echo.
echo   Frontend:  http://localhost:9300
echo   Backend:   http://localhost:9301/api
echo   Database:  localhost:5432
echo.
echo Database credentials:
echo   Username:  postgres
echo   Password:  postgres
echo   Database:  wedding_invitations
echo.
echo Quick commands:
echo   View logs:       docker-compose logs -f
echo   Stop services:   docker-compose down
echo   Restart:         docker-compose restart
echo.
echo Next steps:
echo   1. Open http://localhost:9300 in your browser
echo   2. Click 'Sign Up' to create an account
echo   3. Create your first wedding event
echo   4. Share the invitation URL with guests
echo.
echo For more information, see:
echo   - SETUP.md for detailed setup instructions
echo   - TESTING_GUIDE.md for testing scenarios
echo   - TROUBLESHOOTING.md for common issues
echo.
echo [OK] Happy wedding planning!
echo.

pause

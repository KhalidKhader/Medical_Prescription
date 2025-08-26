@echo off
REM Escribe Triage - Deployment Script for Windows
REM This script handles deployment of the medical prescription AI system

echo 🚀 Starting Escribe Triage deployment...

REM Check if we're in the right directory
if not exist "pyproject.toml" (
    echo ❌ Error: pyproject.toml not found. Please run this script from the project root.
    pause
    exit /b 1
)

REM Check if Poetry is installed
poetry --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Poetry is not installed. Please install Poetry first.
    echo    curl -sSL https://install.python-poetry.org ^| python3 -
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ⚠️  Warning: .env file not found. Please create one from .env.example
    echo    copy .env.example .env
    echo    Then edit .env with your actual configuration values.
    set /p continue="Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        pause
        exit /b 1
    )
)

echo 📦 Installing dependencies...
poetry install --no-dev

echo 🧪 Running tests...
poetry run pytest tests/ -v --cov=src --cov-report=html

echo 🔍 Running code quality checks...
poetry run black --check src/
poetry run isort --check-only src/
poetry run ruff check src/
poetry run mypy src/

echo 🏗️  Building project...
poetry build

echo ✅ Deployment preparation completed successfully!
echo.
echo To start the application:
echo   poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
echo.
echo Or use the Makefile:
echo   make dev
echo.
echo API documentation will be available at:
echo   http://localhost:8000/docs
echo.
pause

@echo off
REM Medical Prescription AI APIs - Windows Batch Commands
REM Alternative to Makefile for Windows users

set POETRY_PATH=C:\Users\khalid.khader\AppData\Roaming\Python\Scripts\poetry.exe

if "%1"=="install" goto install
if "%1"=="dev" goto dev
if "%1"=="test" goto test
if "%1"=="test-system" goto test-system
if "%1"=="test-gemini" goto test-gemini
if "%1"=="test-rxnorm" goto test-rxnorm
if "%1"=="test-json-utils" goto test-json-utils
if "%1"=="test-image-preprocessing" goto test-image-preprocessing
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="clean" goto clean
if "%1"=="help" goto help

echo Unknown command: %1
echo Run "run.bat help" for available commands
goto end

:install
echo Installing dependencies with Poetry...
%POETRY_PATH% install
goto end

:dev
echo Starting development server...
%POETRY_PATH% run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
goto end

:test
echo Running tests with coverage...
%POETRY_PATH% run pytest tests/ -v --cov=src --cov-report=html --cov-report=term
goto end

:test-system
echo Running comprehensive system tests...
%POETRY_PATH% run python test_system_improvements.py
goto end

:test-gemini
echo Testing Gemini service...
%POETRY_PATH% run python -c "from src.core.services.gemini.gemini import gemini_service; import asyncio; print(asyncio.run(gemini_service.test_connection()))"
goto end

:test-rxnorm
echo Testing RxNorm service...
%POETRY_PATH% run python -c "from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service; import asyncio; print(asyncio.run(rxnorm_service.test_connection()))"
goto end

:test-json-utils
echo Testing JSON utilities...
%POETRY_PATH% run python -c "from src.modules.ai_agents.utils.json import parse_json; print('JSON utilities loaded:', parse_json('{\"test\": true}'))"
goto end

:test-image-preprocessing
echo Testing image preprocessing...
%POETRY_PATH% run python -c "from src.core.services.image.preprocessing import image_preprocessor; print('Image preprocessor loaded successfully')"
goto end

:lint
echo Linting code...
%POETRY_PATH% run ruff check src/
%POETRY_PATH% run mypy src/
goto end

:format
echo Formatting code...
%POETRY_PATH% run black src/ tests/
%POETRY_PATH% run isort src/ tests/
goto end

:clean
echo Cleaning temporary files...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"
del /s /q *.pyc 2>nul
if exist .coverage del .coverage
if exist htmlcov rmdir /s /q htmlcov
goto end

:help
echo Medical Prescription AI APIs - Windows Commands
echo.
echo Available commands:
echo   run.bat install                    - Install dependencies
echo   run.bat dev                        - Start development server
echo   run.bat test                       - Run all tests with coverage
echo   run.bat test-system                - Run comprehensive system tests
echo   run.bat test-gemini                - Test Gemini API connection
echo   run.bat test-rxnorm                - Test RxNorm database connection
echo   run.bat test-json-utils            - Test JSON utilities
echo   run.bat test-image-preprocessing   - Test image preprocessing
echo   run.bat lint                       - Lint code
echo   run.bat format                     - Format code
echo   run.bat clean                      - Clean temporary files
echo   run.bat help                       - Show this help
echo.
echo Setup Instructions:
echo   1. Copy env_configuration_template to .env
echo   2. Edit .env with your API keys
echo   3. Run: run.bat install
echo   4. Run: run.bat dev
echo.
goto end

:end

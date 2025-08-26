#!/bin/bash

# Escribe Triage - Deployment Script
# This script handles deployment of the medical prescription AI system

set -e

echo "🚀 Starting Escribe Triage deployment..."

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Error: Poetry is not installed. Please install Poetry first."
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found. Please create one from .env.example"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your actual configuration values."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Installing dependencies..."
poetry install --no-dev

echo "🧪 Running tests..."
poetry run pytest tests/ -v --cov=src --cov-report=html

echo "🔍 Running code quality checks..."
poetry run black --check src/
poetry run isort --check-only src/
poetry run ruff check src/
poetry run mypy src/

echo "🏗️  Building project..."
poetry build

echo "✅ Deployment preparation completed successfully!"
echo ""
echo "To start the application:"
echo "  poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "Or use the Makefile:"
echo "  make dev"
echo ""
echo "API documentation will be available at:"
echo "  http://localhost:8000/docs"

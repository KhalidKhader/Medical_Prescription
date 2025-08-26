# Makefile for Escribe Triage - Medical Prescription AI APIs

.PHONY: install dev test lint format clean auth docker-up docker-down

# Install dependencies
install:
	poetry install

# Run development server
dev:
	poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	poetry run pytest tests/ -v --cov=src --cov-report=html

# Test specific agents
test-agents:
	poetry run pytest tests/agents/ -v

# Test integration
test-integration:
	poetry run pytest tests/integration/ -v

# Lint code
lint:
	poetry run ruff check src/
	poetry run mypy src/

# Format code
format:
	poetry run black src/
	poetry run isort src/

# Clean cache and temporary files
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf .coverage htmlcov/

# Google Cloud authentication
auth:
	gcloud auth application-default login

# Neo4j RxNorm operations
docker-up:
	docker-compose up -d neo4j

docker-down:
	docker-compose down

rxnorm-status:
	docker ps | grep neo4j

rxnorm-logs:
	docker logs neo4j-container

# Test RxNorm connectivity
test-rxnorm:
	poetry run python -c "from src.core.services.neo4j.rxnorm_rag_service import test_connection; test_connection()"

# Development utilities
deps-update:
	poetry update

deps-export:
	poetry export -f requirements.txt --output requirements.txt --without-hashes

# Gemini API testing
test-gemini:
	poetry run python -c "from src.core.services.gemini.gemini import test_gemini_connection; test_gemini_connection()"

# Health checks
health:
	curl http://localhost:8000/api/v1/health/

health-details:
	curl http://localhost:8000/api/v1/health/service/gemini

# Database operations
db-backup:
	docker exec neo4j-container neo4j-admin dump --database=neo4j --to=/backups/

db-restore:
	docker exec neo4j-container neo4j-admin load --from=/backups/ --database=neo4j --force

# Production deployment
build:
	poetry build

deploy:
	poetry run gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Documentation
docs:
	poetry run pdoc --html src --output-dir docs/

# Security
security-scan:
	poetry run bandit -r src/

audit-deps:
	poetry audit

# Performance testing
benchmark:
	poetry run locust -f tests/performance/locustfile.py --host=http://localhost:8000

# Code quality
quality:
	poetry run black --check src/
	poetry run isort --check-only src/
	poetry run ruff check src/
	poetry run mypy src/

# Git operations
git-setup:
	git remote add origin https://khalidkhader2@bitbucket.org/aplosy/escribe-triage.git
	git branch -M main
	git push -u origin main

git-push:
	git add .
	git commit -m "Update project for escribe-triage repository"
	git push origin main


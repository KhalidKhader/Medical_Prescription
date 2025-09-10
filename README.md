# Escribe Triage - Medical Prescription AI APIs

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Poetry](https://img.shields.io/badge/poetry-1.0+-orange.svg)](https://python-poetry.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

Escribe Triage is an AI-powered medical prescription analysis system that converts handwritten medical prescriptions into structured data using advanced computer vision and natural language processing. The system leverages Google Gemini 2.5 Pro for image analysis and integrates with RxNorm Knowledge Graph via Neo4j for accurate drug information.

## 🚀 Features

- **AI-Powered Prescription Analysis**: Handwritten prescription image processing using Google Gemini 2.5 Pro
- **Multi-Agent Architecture**: Specialized AI agents for different prescription components (patient info, drugs, prescriber, etc.)
- **RxNorm Integration**: Comprehensive drug database integration via Neo4j Knowledge Graph
- **Real-time Processing**: Fast prescription analysis with configurable timeouts
- **Compliance Ready**: HIPAA and PIPEDA compliant data handling
- **Observability**: Complete tracing and monitoring with LangFuse
- **RESTful API**: Clean FastAPI endpoints for easy integration

## 🏗️ Architecture

### System Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Image Extractor │    │ Patient Info     │    │ Drugs           │
│ Agent           │───▶│ Agent            │───▶│ Agent           │
│ (Gemini Vision) │    │ (Validation)     │    │ (RxNorm RAG)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Prescriber      │    │ Hallucination    │    │ Spanish         │
│ Agent           │    │ Detection        │    │ Translation     │
│ (Validation)    │    │ Agent            │    │ Agent           │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Technology Stack

- **Backend**: FastAPI with Python 3.11+
- **AI Models**: Google Gemini 2.5 Pro (Vision & Text)
- **Database**: Neo4j with RxNorm Knowledge Graph
- **Agent Framework**: LangChain + LangGraph
- **Observability**: LangFuse for tracing and monitoring
- **Dependency Management**: Poetry
- **Image Processing**: Pillow for image preprocessing

## 📋 Prerequisites

- Python 3.11 or higher
- Poetry for dependency management
- Neo4j database (local or remote)
- Google Gemini API key
- LangFuse account for observability

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone https://khalidkhader2@bitbucket.org/aplosy/escribe-triage.git
cd escribe-triage
```

### 2. Install Dependencies

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Configure Poetry to create virtual environments in project directory
poetry config virtualenvs.in-project true

# Install project dependencies
poetry install
```

### 3. Environment Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Configure the following environment variables in your `.env` file:

```bash
# Required API Keys and Credentials
GOOGLE_API_KEY=           # Your Google Gemini API key from https://makersuite.google.com/app/apikey
LANGFUSE_SECRET_KEY=      # Format: sk-lf-xxxxxxxx from https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=      # Format: pk-lf-xxxxxxxx from https://cloud.langfuse.com

# Neo4j Database Configuration
NEO4J_URI=bolt://localhost:7687   # Your Neo4j database URI
NEO4J_USER=neo4j                  # Database username (default: neo4j)
NEO4J_PASSWORD=your-secure-pass   # Strong password for Neo4j

# Optional: AI Model Configuration
GEMINI_MODEL_PRIMARY=gemini-2.5-pro-latest      # Primary model
GEMINI_MODEL_SECONDARY=gemini-1.5-pro-latest    # Fallback model 1
GEMINI_MODEL_FALLBACK=gemini-1.5-flash-latest   # Fallback model 2

# Optional: Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id    # Only if using VertexAI
VERTIX_AI_PROJECT_ID=your-project-id    # Only if using VertexAI
GOOGLE_GENAI_USE_VERTEXAI=false        # Set to true if using VertexAI
```

⚠️ **Security Note**: 
- Never commit `.env` file to version control
- Use strong, unique passwords for all credentials
- Rotate API keys regularly
- Use environment-specific files (`.env.development`, `.env.production`)

# Application Settings
APP_NAME=Escribe Triage
APP_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### 1. Start the Application

```bash
# Activate virtual environment
poetry shell

# Run development server
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Access the API

- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health/
- **Root Endpoint**: http://localhost:8000/

### 3. Test with Sample Data

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health/

# Test prescription processing (example)
curl -X POST "http://localhost:8000/api/v1/prescriptions/process" \
  -H "Content-Type: application/json" \
  -d '{"image_base64": "base64_encoded_image_data"}'
```

## 📚 API Endpoints

### Health Monitoring

- `GET /api/v1/health/` - Comprehensive system health check
- `GET /api/v1/health/service/{service_name}` - Individual service health
- `GET /api/v1/health/ready` - Readiness probe
- `GET /api/v1/health/live` - Liveness probe

### Prescription Processing

- `POST /api/v1/prescriptions/process` - Process prescription image
- `GET /api/v1/prescriptions/{prescription_id}` - Get prescription details
- `GET /api/v1/prescriptions/` - List all prescriptions

## 🔧 Development

### Project Structure

```
escribe-triage/
├── src/
│   ├── core/                    # Core services and configuration
│   │   ├── services/           # External service integrations
│   │   │   ├── gemini/        # Google Gemini AI service
│   │   │   ├── neo4j/         # RxNorm Knowledge Graph
│   │   │   └── image/         # Image processing utilities
│   │   └── settings/          # Configuration management
│   ├── modules/                # Application modules
│   │   ├── ai_agents/         # AI agent implementations
│   │   ├── prescriptions_management/  # Prescription processing
│   │   └── system_health_management/  # Health monitoring
│   └── main.py                # FastAPI application entry point
├── tests/                      # Test suite
├── pyproject.toml             # Poetry configuration
├── Makefile                   # Development automation
└── README.md                  # This file
```

### Available Commands

```bash
# Development Environment Setup
poetry install                     # Install all dependencies
poetry shell                      # Activate virtual environment
poetry update                     # Update dependencies to latest versions
poetry add package_name           # Add new dependency
poetry add -D package_name        # Add development dependency

# Running the Application
poetry run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000  # Development server with hot reload
poetry run python src/main.py                                         # Run without reload
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000           # Production server

# Database Management
poetry run python scripts/setup_neo4j.py   # Initialize Neo4j database
poetry run python scripts/load_rxnorm.py   # Load RxNorm data into Neo4j

# Testing and Quality
poetry run pytest                          # Run all tests
poetry run pytest -v                       # Verbose test output
poetry run pytest --cov=src               # Test coverage
poetry run black src/                     # Format code
poetry run flake8 src/                    # Lint code
poetry run mypy src/                      # Type checking
poetry run safety check                   # Security check

# Cleaning and Maintenance
poetry run python scripts/clean.py        # Clean temporary files
poetry cache clear --all .                # Clear Poetry cache
poetry env remove --all                   # Remove all virtual environments

# Docker Operations
docker-compose up -d                      # Start all services
docker-compose down                       # Stop all services
docker-compose logs -f                    # View logs

# Health Checks
poetry run python scripts/health_check.py # Run system health check
poetry run python scripts/verify_env.py   # Verify environment setup
```

### Running in Different Environments

#### Development
```bash
# Start with hot reload and debug logging
poetry run uvicorn src.main:app \
    --reload \
    --host 0.0.0.0 \
    --port 8000 \
    --log-level debug \
    --env-file .env.development
```

#### Production
```bash
# Start with optimized settings
poetry run uvicorn src.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --log-level info \
    --env-file .env.production \
    --proxy-headers \
    --forwarded-allow-ips '*'
```

#### Testing
```bash
# Run with test configuration
poetry run uvicorn src.main:app \
    --port 8001 \
    --env-file .env.test
```

### Environment Management
```bash
# Create new environment
poetry env use python3.11

# Show current environment info
poetry env info

# List all environments
poetry env list

# Export dependencies
poetry export -f requirements.txt --output requirements.txt
```

### Adding New AI Agents

1. Create agent directory in `src/modules/ai_agents/`
2. Implement `agent.py`, `prompts.py`, and `tools.py`
3. Add agent to workflow orchestrator
4. Update health monitoring

## 🧪 Testing

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=html

# Run specific test categories
poetry run pytest tests/unit/ -v
poetry run pytest tests/integration/ -v
```

##  Monitoring & Observability

### Health Checks

The system provides comprehensive health monitoring for:
- Google Gemini API connectivity
- Neo4j RxNorm database status
- LangFuse observability service
- System resource utilization

### LangFuse Integration

- Complete agent execution tracing
- Performance metrics and analytics
- Error tracking and debugging
- Custom event logging

## 🔒 Security & Compliance

- **Data Encryption**: AES-256 encryption for sensitive data
- **Access Control**: Role-based access control (RBAC)
- **Audit Logging**: Complete audit trail for compliance
- **HIPAA Ready**: Healthcare data protection standards
- **PIPEDA Compliant**: Canadian privacy regulations

## 🚀 Deployment

### Docker Deployment

```bash
# Build Docker image
docker build -t escribe-triage .

# Run container
docker run -p 8000:8000 escribe-triage
```

### Production Considerations

- Use production-grade Neo4j instance
- Configure proper SSL/TLS certificates
- Set up monitoring and alerting
- Implement rate limiting
- Use secrets management for API keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the API documentation at `/docs`

## 🔄 Changelog

### Version 1.0.0
- Initial release with core prescription processing
- Google Gemini 2.5 Pro integration
- RxNorm Knowledge Graph integration
- Multi-agent architecture
- Comprehensive health monitoring
- LangFuse observability integration

---

**Note**: This system processes medical data and should be used in compliance with relevant healthcare regulations and privacy laws.
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

Configure the following environment variables:

```bash
# Google Gemini Configuration
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL_PRIMARY=gemini-2.5-pro-latest
GEMINI_MODEL_SECONDARY=gemini-2.5-pro-latest
GEMINI_MODEL_FALLBACK=gemini-2.5-pro-latest

# Neo4j Configuration (RxNorm KG)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# LangFuse Configuration (Observability)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://us.cloud.langfuse.com

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
# Install dependencies
make install

# Run development server
make dev

# Run tests
make test

# Code formatting
make format

# Linting
make lint

# Clean temporary files
make clean
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

## 📊 Monitoring & Observability

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


"""Configuration management for Medical Prescription AI APIs.

This module provides centralized configuration management using Pydantic Settings,
handling all environment variables and application settings for the medical
SOAP generation microservice.
"""

from functools import lru_cache
from typing import List, Optional, Any

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # =============================================================================
    # Application Settings
    # =============================================================================
    app_name: str = Field(default="medical-prescription-ai-apis", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # =============================================================================
    # Google Gemini Configuration
    # =============================================================================
    google_api_key: str = Field(description="Google Gemini API key - REQUIRED")
    gemini_model_primary: str = Field(default="gemini-1.5-pro-latest", description="Primary Gemini model")
    gemini_model_secondary: str = Field(default="gemini-1.5-flash-latest", description="Secondary Gemini model")
    gemini_model_fallback: str = Field(default="gemini-1.0-pro-latest", description="Fallback Gemini model")
    gemini_temperature: float = Field(default=0.0, description="Gemini model temperature")
    gemini_max_tokens: int = Field(default=8192, description="Gemini max output tokens")
    
    # =============================================================================
    # Neo4j Configuration (RxNorm KG)
    # =============================================================================
    neo4j_uri: str = Field(default="bolt://localhost:7689", description="Neo4j URI")
    neo4j_user: str = Field(default="neo4j", description="Neo4j user")
    neo4j_password: str = Field(default="rxnorm2025", description="Neo4j password")
    neo4j_database: str = Field(default="neo4j", description="Neo4j database")
    neo4j_max_connection_lifetime: int = Field(default=30, description="Neo4j max connection lifetime in seconds")
    neo4j_max_connections: int = Field(default=50, description="Neo4j max connection pool size")
    neo4j_connection_timeout: int = Field(default=30, description="Neo4j connection timeout in seconds")
    
    # =============================================================================
    # Image Processing Configuration
    # =============================================================================
    max_image_size_mb: int = Field(default=10, description="Maximum image size in MB")
    supported_image_formats: str = Field(default="jpg,jpeg,png,pdf", description="Supported image formats (comma-separated)")
    image_processing_timeout: int = Field(default=30, description="Image processing timeout in seconds")
    
    # =============================================================================
    # Agent Configuration
    # =============================================================================
    max_agent_retries: int = Field(default=3, description="Maximum agent retry attempts")
    agent_timeout_seconds: int = Field(default=60, description="Agent timeout in seconds")
    json_repair_enabled: bool = Field(default=True, description="Enable JSON repair functionality")

    # =============================================================================
    # LangFuse Configuration (Observability)
    # =============================================================================
    langfuse_secret_key: str = Field(description="LangFuse secret key - REQUIRED")
    langfuse_public_key: str = Field(description="LangFuse public key - REQUIRED")
    langfuse_host: str = Field(default="https://us.cloud.langfuse.com", description="LangFuse host")
    langfuse_timeout: int = Field(default=25, description="LangFuse request timeout in seconds")
    langfuse_enabled: bool = Field(default=True, description="Enable LangFuse observability (set to false if network issues)")

    # =============================================================================
    # CORS Configuration
    # =============================================================================
    cors_origins: str = Field(default="http://localhost:3000,http://localhost:8000", description="CORS allowed origins (comma-separated)")

  
    # =============================================================================
    # Validators
    # =============================================================================
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of {allowed_levels}")
        return v.upper()

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True,
        use_enum_values=True,
    )
    
    @property
    def supported_image_formats_list(self) -> List[str]:
        """Get supported image formats as a list"""
        return [fmt.strip() for fmt in self.supported_image_formats.split(",")]
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in getattr(self, 'cors_origins', 'http://localhost:3000,http://localhost:8000').split(",")]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
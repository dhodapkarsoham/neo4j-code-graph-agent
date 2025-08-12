"""Configuration management for MCP Code Graph Agent."""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"
    azure_openai_deployment_name: Optional[str] = None
    
    # MCP Server Configuration
    mcp_server_port: int = 3000
    mcp_server_host: str = "localhost"
    
    # Application Configuration
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore'
    )


settings = Settings()

# Debug: Print settings to see if they're loaded correctly
import logging
logger = logging.getLogger(__name__)
logger.info(f"Azure OpenAI API Key: {'Set' if settings.azure_openai_api_key else 'Not set'}")
logger.info(f"Azure OpenAI Endpoint: {'Set' if settings.azure_openai_endpoint else 'Not set'}")
logger.info(f"Azure OpenAI Deployment: {'Set' if settings.azure_openai_deployment_name else 'Not set'}")
logger.info(f"Env file path: {Path(__file__).parent.parent / '.env'}")
logger.info(f"Env file exists: {(Path(__file__).parent.parent / '.env').exists()}")

"""Tests for configuration management."""

import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from src.config import Settings


class TestSettings:
    """Test cases for Settings class."""

    def test_default_settings(self):
        """Test that default settings are properly set."""
        with patch("builtins.open", mock_open(read_data="")):
            settings = Settings()

            # Test Neo4j defaults
            assert settings.neo4j_uri == "bolt://localhost:7687"
            assert settings.neo4j_user == "neo4j"
            assert settings.neo4j_password == "password"
            assert settings.neo4j_database == "neo4j"

            # Test Azure OpenAI defaults
            assert settings.azure_openai_api_version == "2024-12-01-preview"
            assert settings.azure_openai_api_key is None
            assert settings.azure_openai_endpoint is None
            assert settings.azure_openai_deployment_name is None

            # Test application defaults
            assert settings.debug is True
            assert settings.host == "0.0.0.0"
            assert settings.port == 8000

    def test_environment_variable_loading(self):
        """Test that environment variables are properly loaded."""
        env_data = """
        NEO4J_URI=bolt://test:7687
        NEO4J_USER=test_user
        NEO4J_PASSWORD=test_password
        AZURE_OPENAI_API_KEY=test_key
        AZURE_OPENAI_ENDPOINT=https://test.openai.azure.com/
        AZURE_OPENAI_DEPLOYMENT_NAME=test_deployment
        DEBUG=false
        PORT=9000
        """

        with patch("builtins.open", mock_open(read_data=env_data)):
            settings = Settings()

            assert settings.neo4j_uri == "bolt://test:7687"
            assert settings.neo4j_user == "test_user"
            assert settings.neo4j_password == "test_password"
            assert settings.azure_openai_api_key == "test_key"
            assert settings.azure_openai_endpoint == "https://test.openai.azure.com/"
            assert settings.azure_openai_deployment_name == "test_deployment"
            assert settings.debug is False
            assert settings.port == 9000

    def test_env_file_path(self):
        """Test that the .env file path is correctly constructed."""
        with patch("builtins.open", mock_open(read_data="")):
            settings = Settings()

            # The env_file should be in the parent directory of src/config.py
            expected_path = Path(__file__).parent.parent.parent / ".env"
            assert settings.model_config.env_file == str(expected_path)

    def test_case_insensitive_loading(self):
        """Test that environment variables are loaded case-insensitively."""
        env_data = """
        neo4j_uri=bolt://test:7687
        AZURE_OPENAI_API_KEY=test_key
        """

        with patch("builtins.open", mock_open(read_data=env_data)):
            settings = Settings()

            # Should load regardless of case
            assert settings.neo4j_uri == "bolt://test:7687"
            assert settings.azure_openai_api_key == "test_key"

    def test_missing_env_file_handling(self):
        """Test that the application handles missing .env file gracefully."""
        with patch("pathlib.Path.exists", return_value=False):
            settings = Settings()

            # Should use defaults when .env file doesn't exist
            assert settings.neo4j_uri == "bolt://localhost:7687"
            assert settings.azure_openai_api_key is None

    def test_invalid_env_file_handling(self):
        """Test that the application handles invalid .env file gracefully."""
        with patch("builtins.open", side_effect=Exception("File not found")):
            settings = Settings()

            # Should use defaults when .env file can't be read
            assert settings.neo4j_uri == "bolt://localhost:7687"
            assert settings.azure_openai_api_key is None


if __name__ == "__main__":
    pytest.main([__file__])

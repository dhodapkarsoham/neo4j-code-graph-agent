"""Tests for LLM integration."""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from typing import List, Dict, Any

from src.llm import AzureOpenAIClient


class TestAzureOpenAIClient:
    """Test cases for LLMClient class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.llm_client = AzureOpenAIClient()

    @patch('src.llm.settings')
    def test_initialize_client_success(self, mock_settings):
        """Test successful client initialization."""
        mock_settings.azure_openai_api_key = "test_key"
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_deployment_name = "test_deployment"
        mock_settings.azure_openai_api_version = "2024-12-01-preview"
        
        with patch('src.llm.AzureOpenAI') as mock_azure_openai:
            mock_client = MagicMock()
            mock_azure_openai.return_value = mock_client
            
            self.llm_client._initialize_client()
            
            assert self.llm_client.client is not None
            mock_azure_openai.assert_called_once_with(
                api_key="test_key",
                api_version="2024-12-01-preview",
                azure_endpoint="https://test.openai.azure.com/"
            )

    @patch('src.llm.settings')
    def test_initialize_client_missing_config(self, mock_settings):
        """Test client initialization with missing configuration."""
        mock_settings.azure_openai_api_key = None
        mock_settings.azure_openai_endpoint = None
        mock_settings.azure_openai_deployment_name = None
        
        self.llm_client._initialize_client()
        
        assert self.llm_client.client is None

    @patch('src.llm.settings')
    def test_initialize_client_exception(self, mock_settings):
        """Test client initialization with exception."""
        mock_settings.azure_openai_api_key = "test_key"
        mock_settings.azure_openai_endpoint = "https://test.openai.azure.com/"
        mock_settings.azure_openai_deployment_name = "test_deployment"
        mock_settings.azure_openai_api_version = "2024-12-01-preview"
        
        with patch('src.llm.AzureOpenAI', side_effect=Exception("Connection failed")):
            self.llm_client._initialize_client()
            
            assert self.llm_client.client is None

    def test_is_configured(self):
        """Test is_configured method."""
        # Test when client is not configured
        self.llm_client.client = None
        assert self.llm_client.is_configured() is False
        
        # Test when client is configured
        self.llm_client.client = MagicMock()
        assert self.llm_client.is_configured() is True

    @patch('src.llm.settings')
    async def test_generate_response_success(self, mock_settings):
        """Test successful response generation."""
        mock_settings.azure_openai_deployment_name = "test_deployment"
        
        self.llm_client.client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        self.llm_client.client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "Hello"}]
        system_prompt = "You are a helpful assistant."
        
        result = await self.llm_client.generate_response(
            messages=messages,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=100
        )
        
        assert result == "Test response"
        self.llm_client.client.chat.completions.create.assert_called_once()

    async def test_generate_response_no_client(self):
        """Test response generation without configured client."""
        self.llm_client.client = None
        
        with pytest.raises(RuntimeError, match="Azure OpenAI client not configured"):
            await self.llm_client.generate_response(messages=[])

    @patch('src.llm.settings')
    async def test_generate_response_exception(self, mock_settings):
        """Test response generation with exception."""
        mock_settings.azure_openai_deployment_name = "test_deployment"
        
        self.llm_client.client = MagicMock()
        self.llm_client.client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception, match="API Error"):
            await self.llm_client.generate_response(messages=[])

    async def test_analyze_query_and_select_tools_no_client(self):
        """Test query analysis without LLM client."""
        self.llm_client.client = None
        
        available_tools = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"},
            {"name": "tool2", "description": "Tool 2", "category": "Test"}
        ]
        
        result = await self.llm_client.analyze_query_and_select_tools(
            "test query", available_tools
        )
        
        assert "understanding" in result
        assert "selected_tools" in result
        assert "intelligence_level" in result
        assert result["intelligence_level"] == "Keyword-based"

    @patch('src.llm.settings')
    async def test_analyze_query_and_select_tools_with_client(self, mock_settings):
        """Test query analysis with LLM client."""
        mock_settings.azure_openai_deployment_name = "test_deployment"
        
        self.llm_client.client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "understanding": "User wants to analyze code",
            "selected_tools": ["tool1"],
            "reasoning": "Tool 1 is relevant",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "llm_analysis": "Step-by-step analysis"
        })
        self.llm_client.client.chat.completions.create.return_value = mock_response
        
        available_tools = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"},
            {"name": "tool2", "description": "Tool 2", "category": "Test"}
        ]
        
        result = await self.llm_client.analyze_query_and_select_tools(
            "analyze code quality", available_tools
        )
        
        assert result["understanding"] == "User wants to analyze code"
        assert result["selected_tools"] == ["tool1"]
        assert result["intelligence_level"] == "LLM-powered"
        assert "llm_reasoning_details" in result

    @patch('src.llm.settings')
    async def test_analyze_query_and_select_tools_invalid_json(self, mock_settings):
        """Test query analysis with invalid JSON response."""
        mock_settings.azure_openai_deployment_name = "test_deployment"
        
        self.llm_client.client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        self.llm_client.client.chat.completions.create.return_value = mock_response
        
        available_tools = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"}
        ]
        
        result = await self.llm_client.analyze_query_and_select_tools(
            "test query", available_tools
        )
        
        # Should fall back to keyword-based selection
        assert result["intelligence_level"] == "Keyword-based"

    def test_fallback_keyword_selection(self):
        """Test fallback keyword-based tool selection."""
        available_tools = [
            {"name": "security_tool", "description": "Security analysis tool", "category": "Security"},
            {"name": "quality_tool", "description": "Code quality tool", "category": "Quality"},
            {"name": "architecture_tool", "description": "Architecture analysis", "category": "Architecture"}
        ]
        
        # Test security-related query
        result = self.llm_client._fallback_keyword_selection("find security vulnerabilities", available_tools)
        assert "security_tool" in result["selected_tools"]
        assert result["intelligence_level"] == "Keyword-based"
        
        # Test quality-related query
        result = self.llm_client._fallback_keyword_selection("analyze code quality", available_tools)
        assert "quality_tool" in result["selected_tools"]
        
        # Test architecture-related query
        result = self.llm_client._fallback_keyword_selection("architectural issues", available_tools)
        assert "architecture_tool" in result["selected_tools"]

    def test_format_tools_for_llm(self):
        """Test formatting tools for LLM consumption."""
        available_tools = [
            {"name": "tool1", "description": "Tool 1 description", "category": "Test"},
            {"name": "tool2", "description": "Tool 2 description", "category": "Custom"}
        ]
        
        formatted = self.llm_client._format_tools_for_llm(available_tools)
        
        assert "tool1" in formatted
        assert "Tool 1 description" in formatted
        assert "tool2" in formatted
        assert "Tool 2 description" in formatted
        assert "Test" in formatted
        assert "Custom" in formatted

    @patch('src.llm.settings')
    async def test_generate_intelligent_response_success(self, mock_settings):
        """Test successful intelligent response generation."""
        mock_settings.azure_openai_deployment_name = "test_deployment"
        
        self.llm_client.client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Intelligent analysis response"
        self.llm_client.client.chat.completions.create.return_value = mock_response
        
        tool_results = [
            {
                "tool_name": "tool1",
                "results": [{"data": "result1"}],
                "result_count": 1
            }
        ]
        
        result = await self.llm_client.generate_intelligent_response(
            "analyze code",
            "quality",
            "Code quality insights",
            tool_results
        )
        
        assert "response" in result
        assert "llm_reasoning" in result
        assert result["response"] == "Intelligent analysis response"

    async def test_generate_intelligent_response_no_client(self):
        """Test intelligent response generation without client."""
        self.llm_client.client = None
        
        tool_results = [{"tool_name": "tool1", "results": [], "result_count": 0}]
        
        result = await self.llm_client.generate_intelligent_response(
            "analyze code",
            "quality",
            "Code quality insights",
            tool_results
        )
        
        # Should fall back to basic response
        assert "response" in result
        assert "Basic analysis" in result["response"]

    def test_prepare_tool_results_context(self):
        """Test preparing tool results context for LLM."""
        tool_results = [
            {
                "tool_name": "tool1",
                "description": "Tool 1",
                "results": [{"file": "file1.py", "score": 10}],
                "result_count": 1
            },
            {
                "tool_name": "tool2",
                "description": "Tool 2",
                "results": [{"file": "file2.py", "score": 5}],
                "result_count": 1
            }
        ]
        
        context = self.llm_client._prepare_tool_results_context(tool_results)
        
        assert "tool1" in context
        assert "Tool 1" in context
        assert "file1.py" in context
        assert "tool2" in context
        assert "Tool 2" in context
        assert "file2.py" in context

    def test_generate_basic_response(self):
        """Test basic response generation."""
        tool_results = [
            {
                "tool_name": "tool1",
                "description": "Tool 1",
                "results": [{"file": "file1.py", "score": 10}],
                "result_count": 1
            }
        ]
        
        response = self.llm_client._generate_basic_response(
            "analyze code",
            "quality",
            "Code quality insights",
            tool_results
        )
        
        assert "Basic analysis" in response
        assert "tool1" in response
        assert "file1.py" in response


if __name__ == "__main__":
    pytest.main([__file__])

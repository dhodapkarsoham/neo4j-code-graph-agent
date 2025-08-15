"""Tests for LangGraph agent."""

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent import CodeGraphAgent


class TestCodeGraphAgent:
    """Test cases for CodeGraphAgent class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = CodeGraphAgent()

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_process_query_success(self, mock_llm_client, mock_tool_registry):
        """Test successful query processing."""
        # Mock tool registry
        mock_tool_registry.list_tools.return_value = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"},
            {"name": "tool2", "description": "Tool 2", "category": "Test"},
        ]

        # Mock LLM client
        mock_llm_client.analyze_query_and_select_tools.return_value = {
            "understanding": "User wants to analyze code",
            "selected_tools": ["tool1"],
            "reasoning": "Tool 1 is relevant",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "llm_analysis": "Step-by-step analysis",
            "intelligence_level": "LLM-powered",
            "llm_reasoning_details": {"prompt": "test"},
        }

        mock_llm_client.generate_intelligent_response.return_value = {
            "response": "Analysis complete",
            "llm_reasoning": {"details": "test"},
        }

        # Mock tool execution
        mock_tool_registry.execute_tool.return_value = {
            "tool_name": "tool1",
            "results": [{"data": "result1"}],
            "result_count": 1,
        }

        result = await self.agent.process_query("analyze code quality")

        assert "response" in result
        assert "reasoning" in result
        assert "tools_used" in result
        assert "understanding" in result
        assert result["response"] == "Analysis complete"
        assert len(result["reasoning"]) > 0

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_process_query_no_tools_selected(
        self, mock_llm_client, mock_tool_registry
    ):
        """Test query processing when no tools are selected."""
        mock_tool_registry.list_tools.return_value = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"}
        ]

        mock_llm_client.analyze_query_and_select_tools.return_value = {
            "understanding": "User query",
            "selected_tools": [],
            "reasoning": "No relevant tools",
            "query_type": "general",
            "expected_insights": "No insights",
            "llm_analysis": "Analysis",
            "intelligence_level": "LLM-powered",
            "llm_reasoning_details": {"prompt": "test"},
        }

        mock_llm_client.generate_intelligent_response.return_value = {
            "response": "No tools available",
            "llm_reasoning": {"details": "test"},
        }

        result = await self.agent.process_query("unrelated query")

        assert "response" in result
        assert result["response"] == "No tools available"
        assert len(result["tools_used"]) == 0

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_process_query_tool_execution_error(
        self, mock_llm_client, mock_tool_registry
    ):
        """Test query processing when tool execution fails."""
        mock_tool_registry.list_tools.return_value = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"}
        ]

        mock_llm_client.analyze_query_and_select_tools.return_value = {
            "understanding": "User wants to analyze code",
            "selected_tools": ["tool1"],
            "reasoning": "Tool 1 is relevant",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "llm_analysis": "Step-by-step analysis",
            "intelligence_level": "LLM-powered",
            "llm_reasoning_details": {"prompt": "test"},
        }

        # Mock tool execution failure
        mock_tool_registry.execute_tool.side_effect = Exception("Database error")

        mock_llm_client.generate_intelligent_response.return_value = {
            "response": "Error occurred",
            "llm_reasoning": {"details": "test"},
        }

        result = await self.agent.process_query("analyze code")

        assert "response" in result
        assert (
            "error" in result["response"].lower()
            or "Error occurred" in result["response"]
        )

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_understand_query_step(self, mock_llm_client, mock_tool_registry):
        """Test the query understanding step."""
        mock_tool_registry.list_tools.return_value = [
            {"name": "tool1", "description": "Tool 1", "category": "Test"}
        ]

        mock_llm_client.analyze_query_and_select_tools.return_value = {
            "understanding": "User wants to analyze code",
            "selected_tools": ["tool1"],
            "reasoning": "Tool 1 is relevant",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "llm_analysis": "Step-by-step analysis",
            "intelligence_level": "LLM-powered",
            "llm_reasoning_details": {"prompt": "test"},
        }

        state = {"user_query": "analyze code quality"}

        result = await self.agent._understand_query(state)

        assert "understanding" in result
        assert "selected_tools" in result
        assert "query_type" in result
        assert "expected_insights" in result
        assert "llm_analysis" in result
        assert "intelligence_level" in result
        assert "llm_reasoning_details" in result
        assert result["selected_tools"] == ["tool1"]

    @patch("src.agent.tool_registry")
    async def test_execute_tools_step(self, mock_tool_registry):
        """Test the tool execution step."""
        mock_tool_registry.execute_tool.return_value = {
            "tool_name": "tool1",
            "results": [{"data": "result1"}],
            "result_count": 1,
        }

        state = {"selected_tools": ["tool1", "tool2"], "understanding": "User query"}

        result = await self.agent._execute_tools(state)

        assert "tool_results" in result
        assert len(result["tool_results"]) == 2
        assert result["tool_results"][0]["tool_name"] == "tool1"
        assert result["tool_results"][1]["tool_name"] == "tool2"

        # Verify tool_registry.execute_tool was called for each tool
        assert mock_tool_registry.execute_tool.call_count == 2

    @patch("src.agent.tool_registry")
    async def test_execute_tools_with_errors(self, mock_tool_registry):
        """Test tool execution with some tools failing."""
        # Mock first tool success, second tool failure
        mock_tool_registry.execute_tool.side_effect = [
            {"tool_name": "tool1", "results": [{"data": "result1"}], "result_count": 1},
            Exception("Database error"),
        ]

        state = {"selected_tools": ["tool1", "tool2"], "understanding": "User query"}

        result = await self.agent._execute_tools(state)

        assert "tool_results" in result
        assert len(result["tool_results"]) == 2

        # First tool should have results
        assert result["tool_results"][0]["tool_name"] == "tool1"
        assert "results" in result["tool_results"][0]

        # Second tool should have error
        assert result["tool_results"][1]["tool_name"] == "tool2"
        assert "error" in result["tool_results"][1]

    @patch("src.agent.llm_client")
    async def test_generate_response_step(self, mock_llm_client):
        """Test the response generation step."""
        mock_llm_client.generate_intelligent_response.return_value = {
            "response": "Analysis complete",
            "llm_reasoning": {"details": "test"},
        }

        state = {
            "user_query": "analyze code",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "tool_results": [
                {
                    "tool_name": "tool1",
                    "results": [{"data": "result1"}],
                    "result_count": 1,
                }
            ],
        }

        result = await self.agent._generate_response(state)

        assert "final_response" in result
        assert "llm_reasoning" in result
        assert result["final_response"] == "Analysis complete"

    @patch("src.agent.llm_client")
    async def test_generate_response_no_llm_client(self, mock_llm_client):
        """Test response generation without LLM client."""
        # Mock LLM client not available
        mock_llm_client.generate_intelligent_response.side_effect = Exception(
            "LLM not available"
        )

        state = {
            "user_query": "analyze code",
            "query_type": "quality",
            "expected_insights": "Code quality insights",
            "tool_results": [
                {
                    "tool_name": "tool1",
                    "results": [{"data": "result1"}],
                    "result_count": 1,
                }
            ],
        }

        result = await self.agent._generate_response(state)

        assert "final_response" in result
        assert "Basic analysis" in result["final_response"]

    def test_agent_workflow_definition(self):
        """Test that the agent workflow is properly defined."""
        # Test that the workflow has the expected nodes
        assert "understand_query" in self.agent.workflow.nodes
        assert "execute_tools" in self.agent.workflow.nodes
        assert "generate_response" in self.agent.workflow.nodes
        assert "end" in self.agent.workflow.nodes

        # Test that the workflow has the expected edges
        edges = list(self.agent.workflow.edges)
        edge_names = [edge[0] for edge in edges]

        assert "understand_query" in edge_names
        assert "execute_tools" in edge_names
        assert "generate_response" in edge_names

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_agent_with_keyword_fallback(
        self, mock_llm_client, mock_tool_registry
    ):
        """Test agent behavior when LLM falls back to keyword selection."""
        mock_tool_registry.list_tools.return_value = [
            {
                "name": "security_tool",
                "description": "Security analysis",
                "category": "Security",
            },
            {
                "name": "quality_tool",
                "description": "Quality analysis",
                "category": "Quality",
            },
        ]

        # Mock LLM client returning keyword-based selection
        mock_llm_client.analyze_query_and_select_tools.return_value = {
            "understanding": "User is asking about security",
            "selected_tools": ["security_tool"],
            "reasoning": "Security-related query",
            "query_type": "security",
            "expected_insights": "Security insights",
            "llm_analysis": "Keyword matching",
            "intelligence_level": "Keyword-based",
            "llm_reasoning_details": {},
        }

        mock_tool_registry.execute_tool.return_value = {
            "tool_name": "security_tool",
            "results": [{"vulnerability": "CVE-2023-1234"}],
            "result_count": 1,
        }

        mock_llm_client.generate_intelligent_response.return_value = {
            "response": "Security analysis complete",
            "llm_reasoning": {"details": "test"},
        }

        result = await self.agent.process_query("find security vulnerabilities")

        assert "response" in result
        assert "Security analysis" in result["response"]
        assert result["reasoning"][0]["intelligence_level"] == "Keyword-based"

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_agent_with_empty_query(self, mock_llm_client, mock_tool_registry):
        """Test agent behavior with empty query."""
        result = await self.agent.process_query("")

        assert "response" in result
        assert (
            "error" in result["response"].lower()
            or "empty" in result["response"].lower()
        )

    @patch("src.agent.tool_registry")
    @patch("src.agent.llm_client")
    async def test_agent_with_none_query(self, mock_llm_client, mock_tool_registry):
        """Test agent behavior with None query."""
        result = await self.agent.process_query(None)

        assert "response" in result
        assert (
            "error" in result["response"].lower()
            or "invalid" in result["response"].lower()
        )


if __name__ == "__main__":
    pytest.main([__file__])

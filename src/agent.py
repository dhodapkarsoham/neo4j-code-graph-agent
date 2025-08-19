"""LangGraph-based agent for orchestrating code analysis tools."""

import logging
from typing import Any, AsyncGenerator, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from src.llm import llm_client
from src.tools import tool_registry

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agentic workflow."""

    user_query: str
    understanding: Dict[str, Any]
    selected_tools: List[str]
    tool_results: List[Dict[str, Any]]
    final_response: str
    reasoning: List[Dict[str, Any]]


class CodeGraphAgent:
    """Intelligent agent that orchestrates code analysis tools to answer user questions."""

    def __init__(self) -> None:
        """Initialize the agent."""
        self.workflow = self._create_workflow()

    def _create_workflow(self) -> Any:
        """Create the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("understand_query", self._understand_query)
        workflow.add_node("execute_tools", self._execute_tools)
        workflow.add_node("generate_response", self._generate_response)

        # Add edges
        workflow.set_entry_point("understand_query")
        workflow.add_edge("understand_query", "execute_tools")
        workflow.add_edge("execute_tools", "generate_response")
        workflow.add_edge("generate_response", END)

        compiled_workflow = workflow.compile()
        return compiled_workflow

    async def _understand_query(self, state: AgentState) -> AgentState:
        """Understand the user query and select appropriate tools."""
        try:
            available_tools = tool_registry.list_tools()
            understanding = await llm_client.analyze_query_and_select_tools(
                state["user_query"], available_tools
            )

            state["understanding"] = understanding
            state["selected_tools"] = understanding.get("selected_tools", [])

            # Add reasoning with LLM details
            reasoning_step = {
                "step": "query_understanding",
                "description": "Analyzed user query and selected tools",
                "understanding": understanding.get("understanding", ""),
                "selected_tools": state["selected_tools"],
                "reasoning": understanding.get("reasoning", ""),
                "query_type": understanding.get("query_type", "general"),
                "expected_insights": understanding.get("expected_insights", ""),
                "llm_analysis": understanding.get("llm_analysis", ""),
                "intelligence_level": understanding.get(
                    "intelligence_level", "LLM-powered"
                ),
                "llm_reasoning_details": understanding.get("llm_reasoning_details", {}),
            }
            state["reasoning"] = [reasoning_step]

        except Exception as e:
            logger.error(f"Error understanding query: {e}")
            state["understanding"] = {"error": str(e)}
            state["selected_tools"] = []
            state["reasoning"] = [{"step": "error", "description": str(e)}]

        return state

    async def _execute_tools(self, state: AgentState) -> AgentState:
        """Execute the selected tools."""
        tool_results = []

        logger.info(f"Executing tools. Selected tools: {state['selected_tools']}")

        # If no tools were selected, log a warning but don't use keyword fallback
        if not state["selected_tools"]:
            logger.warning("No tools selected by LLM. This may indicate an issue with tool selection.")
            logger.info("Available tools: " + ", ".join([t["name"] for t in tool_registry.list_tools()]))

        for tool_name in state["selected_tools"]:
            try:
                # Special handling for text2cypher tool - pass the user query as parameter and use async
                if tool_name == "text2cypher":
                    result = await tool_registry.async_execute_tool(tool_name, {"question": state["user_query"]})
                else:
                    result = tool_registry.execute_tool(tool_name)
                tool_results.append(result)

                # Add reasoning
                reasoning_step = {
                    "step": "tool_execution",
                    "tool_name": tool_name,
                    "description": f"Executed {tool_name}",
                    "result_count": result.get("result_count", 0),
                    "category": result.get("category", ""),
                    "db_metrics": result.get("db_metrics"),
                }
                
                # Add text2cypher specific data for UI display
                if tool_name == "text2cypher":
                    reasoning_step.update({
                        "generated_query": result.get("generated_query", ""),
                        "explanation": result.get("explanation", ""),
                        "results": result.get("results", []),
                    })

                state["reasoning"].append(reasoning_step)

            except Exception as e:
                logger.error(f"Error executing tool {tool_name}: {e}")
                tool_results.append(
                    {"tool_name": tool_name, "error": str(e), "results": []}
                )

        state["tool_results"] = tool_results
        
        # Ensure the state is properly updated with tool results
        logger.info(f"Tool execution completed. Results count: {len(tool_results)}")
        for result in tool_results:
            logger.info(f"  Tool: {result.get('tool_name')}, Results: {result.get('result_count', 0)}")
        
        return state

    async def _generate_response(self, state: AgentState) -> AgentState:
        """Generate final response based on tool results."""
        try:
            # Get query type and expected insights from understanding
            query_type = state["understanding"].get("query_type", "general")
            expected_insights = state["understanding"].get("expected_insights", "")

            # Use intelligent response generation
            response_data = await llm_client.generate_intelligent_response(
                user_query=state["user_query"],
                tool_results=state["tool_results"],
                query_type=query_type,
                expected_insights=expected_insights,
            )

            state["final_response"] = response_data["response"]

            # Add reasoning with LLM details
            reasoning_step = {
                "step": "response_generation",
                "description": "Generated intelligent, contextual response",
                "response_length": len(response_data["response"]),
                "tools_used": len(state["tool_results"]),
                "query_type": query_type,
                "intelligence_level": response_data["llm_reasoning"][
                    "intelligence_level"
                ],
                "llm_reasoning": response_data["llm_reasoning"],
            }
            state["reasoning"].append(reasoning_step)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            state["final_response"] = f"Error generating response: {e}"

        return state



    def _prepare_context(self, state: AgentState) -> str:
        """Prepare context from tool results for LLM."""
        context_parts = []

        if not state["tool_results"]:
            return "No tool results available. Please try a different query or check if the selected tools are working properly."

        for result in state["tool_results"]:
            if "error" in result:
                context_parts.append(
                    f"Tool {result['tool_name']}: Error - {result['error']}"
                )
                continue

            context_parts.append(f"Tool: {result['tool_name']}")
            context_parts.append(f"Description: {result['description']}")
            context_parts.append(f"Category: {result['category']}")
            context_parts.append(f"Results ({result['result_count']} items):")

            # Add all results (no limitation)
            for i, item in enumerate(result["results"]):
                context_parts.append(f"  {i+1}. {item}")

            context_parts.append("")

        return "\n".join(context_parts)

    async def process_query(self, user_query: str) -> Dict[str, Any]:
        """Process a user query through the agent workflow."""
        initial_state = AgentState(
            user_query=user_query,
            understanding={},
            selected_tools=[],
            tool_results=[],
            final_response="",
            reasoning=[],
        )

        try:
            final_state = await self.workflow.ainvoke(initial_state)
            
            # Ensure tool_results is included in the response
            tool_results = final_state.get("tool_results", [])
            logger.info(f"Final state tool_results count: {len(tool_results)}")
            
            return {
                "query": user_query,
                "response": final_state["final_response"],
                "understanding": final_state["understanding"],
                "tools_used": final_state["selected_tools"],
                "tool_results": tool_results,
                "reasoning": final_state["reasoning"],
            }
        except Exception as e:
            logger.error(f"Error in agent workflow: {e}")
            return {
                "query": user_query,
                "response": f"Error processing query: {e}",
                "understanding": {"error": str(e)},
                "tools_used": [],
                "tool_results": [],
                "reasoning": [{"step": "workflow_error", "description": str(e)}],
            }

    async def stream_query(
        self, user_query: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agent workflow events for a user query as an async generator.

        Yields structured events that the UI can render in real-time.
        """
        # Session start
        yield {"type": "session_started", "data": {"query": user_query}}

        # Initialize state
        state = AgentState(
            user_query=user_query,
            understanding={},
            selected_tools=[],
            tool_results=[],
            final_response="",
            reasoning=[],
        )

        # Understand query
        try:
            state = await self._understand_query(state)
            understanding = state.get("understanding", {})
            reasoning_step = state.get("reasoning", [{}])[0]
            yield {
                "type": "llm_reasoning_update",
                "data": {
                    "understanding": understanding.get("understanding", ""),
                    "reasoning": understanding.get("reasoning", ""),
                    "llm_analysis": understanding.get("llm_analysis", ""),
                    "intelligence_level": understanding.get(
                        "intelligence_level", "LLM-powered"
                    ),
                    "llm_reasoning_details": understanding.get(
                        "llm_reasoning_details", {}
                    ),
                },
            }
            yield {
                "type": "tools_selected",
                "data": {"tools": state.get("selected_tools", [])},
            }
        except Exception as e:
            logger.error(f"Error understanding query (stream): {e}")
            yield {"type": "error", "data": {"message": "Failed to analyze query."}}
            return

        # Execute tools one by one to stream progress
        tool_results: List[Dict[str, Any]] = []
        selected_tools = state.get("selected_tools", [])
        if not selected_tools:
            # No fallback - rely on LLM selection
            logger.warning("No tools selected by LLM in streaming mode")
            yield {
                "type": "tools_selected",
                "data": {"tools": [], "fallback": False},
            }

        for tool_name in selected_tools:
            # Include the tool's Cypher for client-side visualization
            try:
                tool_obj = tool_registry.get_tool_by_name(tool_name)
                tool_cypher = tool_obj.query if tool_obj else None
            except Exception:
                tool_cypher = None
            yield {
                "type": "tool_execution_start",
                "data": {"tool": tool_name, "cypher": tool_cypher},
            }
            try:
                # Special handling for text2cypher tool - pass the user query as parameter and use async
                if tool_name == "text2cypher":
                    result = await tool_registry.async_execute_tool(tool_name, {"question": user_query})

                else:
                    result = tool_registry.execute_tool(tool_name)
                tool_results.append(result)
                # Append reasoning step to state
                reasoning_step = {
                    "step": "tool_execution",
                    "tool_name": tool_name,
                    "description": f"Executed {tool_name}",
                    "result_count": result.get("result_count", 0),
                    "category": result.get("category", ""),
                    "db_metrics": result.get("db_metrics"),
                }
                
                # Add text2cypher specific data for UI display
                if tool_name == "text2cypher":
                    reasoning_step.update({
                        "generated_query": result.get("generated_query", ""),
                        "explanation": result.get("explanation", ""),
                        "results": result.get("results", []),
                    })

                
                state.setdefault("reasoning", []).append(reasoning_step)
                # Stream summarized result (avoid huge payloads)
                summary = {
                    "tool": tool_name,
                    "result_count": result.get("result_count", 0),
                    "category": result.get("category", ""),
                    "db_metrics": result.get("db_metrics"),
                }
                
                # Add text2cypher specific data for UI display
                if tool_name == "text2cypher":
                    summary.update({
                        "generated_query": result.get("generated_query", ""),
                        "explanation": result.get("explanation", ""),
                        "results": result.get("results", [])[:10],  # Limit to first 10 results for streaming
                    })

                
                yield {"type": "tool_execution_result", "data": summary}
            except Exception as e:
                logger.error(f"Error executing tool {tool_name} (stream): {e}")
                tool_results.append(
                    {"tool_name": tool_name, "error": "Execution error", "results": []}
                )
                yield {
                    "type": "tool_execution_error",
                    "data": {"tool": tool_name, "message": "Execution error"},
                }

        state["tool_results"] = tool_results

        # Generate response and stream chunks
        try:
            query_type = state.get("understanding", {}).get("query_type", "general")
            expected_insights = state.get("understanding", {}).get(
                "expected_insights", ""
            )
            response_data = await llm_client.generate_intelligent_response(
                user_query=user_query,
                tool_results=tool_results,
                query_type=query_type,
                expected_insights=expected_insights,
            )
            full_text: str = response_data.get("response", "")

            # Stream as paragraph chunks for now
            chunks = [c for c in full_text.split("\n\n") if c.strip()]
            accumulated = ""
            for chunk in chunks:
                accumulated = accumulated + ("\n\n" if accumulated else "") + chunk
                yield {"type": "llm_response_update", "data": {"chunk": chunk}}

            # Append response generation reasoning to state and send a reasoning update
            state.setdefault("reasoning", []).append(
                {
                    "step": "response_generation",
                    "description": "Generated intelligent, contextual response",
                    "response_length": len(full_text),
                    "tools_used": len(tool_results),
                    "query_type": query_type,
                    "intelligence_level": response_data.get("llm_reasoning", {}).get(
                        "intelligence_level", "LLM-powered"
                    ),
                    "llm_reasoning": response_data.get("llm_reasoning", {}),
                }
            )
            yield {"type": "reasoning_append", "data": state["reasoning"][-1]}

            yield {
                "type": "final_response",
                "data": {"text": full_text, "reasoning": state.get("reasoning", [])},
            }
        except Exception as e:
            logger.error(f"Error generating response (stream): {e}")
            yield {"type": "error", "data": {"message": "Failed to generate response."}}
            return

        yield {"type": "session_complete", "data": {}}


# Global agent instance
agent = CodeGraphAgent()

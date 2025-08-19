"""Azure OpenAI LLM client for the agent."""

import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

from src.config import settings

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI client for LLM interactions."""

    def __init__(self) -> None:
        """Initialize Azure OpenAI client."""
        self.client: Optional[Any] = None
        self.last_metrics: Optional[Dict[str, Any]] = None
        # Lightweight status tracking for health endpoint and UI
        self.status: Dict[str, Any] = {
            "configured": False,
            "initial_check_done": False,
            "last_success_at": None,
            "last_error_at": None,
            "last_error_message": None,
        }
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the Azure OpenAI client."""
        logger.info(
            f"Azure OpenAI API Key: {'Set' if settings.azure_openai_api_key else 'Not set'}"
        )
        logger.info(
            f"Azure OpenAI Endpoint: {'Set' if settings.azure_openai_endpoint else 'Not set'}"
        )
        logger.info(
            f"Azure OpenAI Deployment: {'Set' if settings.azure_openai_deployment_name else 'Not set'}"
        )

        if not all(
            [
                settings.azure_openai_api_key,
                settings.azure_openai_endpoint,
                settings.azure_openai_deployment_name,
            ]
        ):
            logger.warning("Azure OpenAI configuration incomplete")
            # Mark as not configured for health reporting
            self.status.update(
                {
                    "configured": False,
                    "initial_check_done": True,
                    "last_error_message": "Azure OpenAI configuration incomplete",
                    "last_error_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return

        try:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
            )
            logger.info("✅ Azure OpenAI client initialized")
            self.status.update({"configured": True})
            # One-time minimal connectivity probe (binary: green/red)
            try:
                _ = self.client.chat.completions.create(
                    model=settings.azure_openai_deployment_name,
                    messages=[{"role": "user", "content": "ping"}],
                    temperature=0,
                    max_tokens=1,
                )
                self.status.update(
                    {
                        "last_success_at": datetime.now(timezone.utc).isoformat(),
                        "initial_check_done": True,
                        "last_error_message": None,
                        "last_error_at": None,
                    }
                )
            except Exception as ping_err:
                logger.warning(f"Azure OpenAI initial ping failed: {ping_err}")
                self.status.update(
                    {
                        "initial_check_done": True,
                        "last_error_message": str(ping_err),
                        "last_error_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure OpenAI client: {e}")
            self.client = None
            self.status.update(
                {
                    "configured": False,
                    "initial_check_done": True,
                    "last_error_message": str(e),
                    "last_error_at": datetime.now(timezone.utc).isoformat(),
                }
            )

    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self.client is not None

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ) -> str:
        """Generate a response using Azure OpenAI."""
        if not self.client:
            raise RuntimeError("Azure OpenAI client not configured")

        try:
            # Prepare messages
            api_messages = []
            if system_prompt:
                api_messages.append({"role": "system", "content": system_prompt})
            api_messages.extend(messages)

            start_time = time.perf_counter()
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment_name,
                messages=api_messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            # Mark success for health reporting
            self.status.update(
                {
                    "last_success_at": datetime.now(timezone.utc).isoformat(),
                    "last_error_message": None,
                    "last_error_at": None,
                }
            )
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            # Extract usage if available
            prompt_tokens = None
            completion_tokens = None
            total_tokens = None
            try:
                usage = getattr(response, "usage", None)
                if usage is not None:
                    prompt_tokens = getattr(usage, "prompt_tokens", None)
                    completion_tokens = getattr(usage, "completion_tokens", None)
                    total_tokens = getattr(usage, "total_tokens", None)
            except Exception:
                pass

            model_name = settings.azure_openai_deployment_name or "unknown"

            self.last_metrics = {
                "model": model_name,
                "latency_ms": latency_ms,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }

            logger.info(
                "LLM metrics | model=%s latency_ms=%.1f prompt_tokens=%s completion_tokens=%s total_tokens=%s",
                model_name,
                latency_ms,
                str(prompt_tokens) if prompt_tokens is not None else "?",
                str(completion_tokens) if completion_tokens is not None else "?",
                str(total_tokens) if total_tokens is not None else "?",
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("LLM response content is None")
            stripped_content: str = content.strip()
            return stripped_content

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Mark error for health reporting
            self.status.update(
                {
                    "last_error_message": str(e),
                    "last_error_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            raise

    # Cost estimation intentionally removed to avoid confusion; keep tokens and latency only

    async def analyze_query_and_select_tools(
        self, user_query: str, available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user query and select appropriate tools using LLM intelligence."""
        logger.info(
            f"Analyzing query: '{user_query}' with {len(available_tools)} available tools"
        )

        if not self.client:
            logger.warning("LLM client not available")
            return {
                "understanding": "LLM client not available",
                "selected_tools": [],
                "reasoning": "Cannot analyze query without LLM",
                "query_type": "error",
                "expected_insights": "Unable to determine",
                "llm_analysis": "LLM client not available",
            }

        logger.info("LLM client is available, proceeding with LLM analysis")

        try:
            # Format tools for LLM consumption
            tools_description = self._format_tools_for_llm(available_tools)

            system_prompt = """You are an expert code analysis agent. Your job is to understand user queries and select the most appropriate tools to answer them.

AVAILABLE TOOLS:
{tools_description}

ANALYSIS INSTRUCTIONS:
1. **Understand the user's intent**: What are they really asking for?
2. **Select relevant tools**: Choose 1-4 tools that best address their needs
3. **Consider tool combinations**: Some queries need multiple tools for comprehensive analysis
4. **Prioritize by relevance**: Don't select tools just because they're available
5. **Use text2cypher for custom questions**: When the user asks specific questions that don't match predefined tools, use text2cypher

TOOL SELECTION PRIORITY:
1. **text2cypher** for specific questions, custom queries, natural language questions, or when user asks about specific entities (ENHANCED with validation and error correction)
2. **Predefined tools** for broad analysis patterns (security overview, quality overview, team overview, architecture overview)
3. **Combinations** when multiple aspects are needed

**PREFER text2cypher WHEN:**
- User asks specific questions (e.g., "What CVEs affect apoc.create.Create?")
- User mentions specific names, files, classes, methods, or dependencies
- User asks "find", "show", "list", "how many", "which", "what" questions
- User wants custom filtering, counting, or listing
- User asks about relationships between specific entities
- User asks security questions about specific dependencies or files
- User asks quality questions about specific methods or classes
- User asks team questions about specific developers or files
- User asks architecture questions about specific components
- No predefined tool perfectly matches the user's specific intent
- User wants to query the database with natural language

RESPONSE FORMAT (JSON):
{{
    "understanding": "Brief explanation of what the user is asking for",
    "selected_tools": ["tool_name_1", "tool_name_2"],
    "reasoning": "Detailed explanation of why these tools were selected",
    "query_type": "security|quality|team|architecture|general|custom",
    "expected_insights": "What kind of insights these tools should provide",
    "llm_analysis": "Step-by-step analysis of how you arrived at this decision"
}}

EXAMPLES:
**text2cypher Examples (PREFERRED for specific questions):**
- "What HIGH severity CVEs affect apoc.create.Create?" → text2cypher (specific dependency + CVE query)
- "Find methods with more than 100 lines" → text2cypher (custom specific query)
- "Show me files that import Jackson" → text2cypher (custom dependency query)
- "Which developers worked on payment code?" → text2cypher (custom specific question)
- "List all files in the authentication module" → text2cypher (custom listing query)
- "How many classes extend BaseController?" → text2cypher (custom counting query)
- "Find files changed in the last month" → text2cypher (custom time-based query)
- "What CVEs are affecting our dependencies?" → text2cypher (specific security query)
- "Show me complex methods in UserService" → text2cypher (specific quality query)
- "Who worked on the login functionality?" → text2cypher (specific team query)

**Predefined Tools Examples (for broad overviews):**
- "Give me a security overview" → security tools (vulnerable_dependencies_summary, cve_impact_analysis)
- "Which files are too complex?" → quality tools (complex_methods_analysis, large_files_analysis)
- "Who works on this module?" → team tools (developer_activity_summary, file_ownership_analysis)
- "Show me architectural issues" → architecture tools (architectural_bottlenecks, co_changed_files_analysis)

**When to use text2cypher (PREFERRED for specific queries):**
- User asks specific questions not covered by predefined tools
- User wants custom filtering, counting, or listing
- User asks "find", "show", "list", "how many", "which", "what" questions
- User mentions specific file names, class names, methods, dependencies, or developers
- User asks about methods, classes, files, or relationships
- User asks security questions about specific dependencies (e.g., "What CVEs affect X?")
- User asks quality questions about specific methods or classes (e.g., "How complex is X?")
- User asks team questions about specific developers or files (e.g., "Who worked on X?")
- User asks architecture questions about specific components (e.g., "What depends on X?")
- No predefined tool perfectly matches the user's specific intent
- User wants to query the database with natural language
- User asks questions that require custom Cypher queries
- User mentions specific entities by name (files, classes, methods, dependencies, developers)

**IMPORTANT:** 
- **ALWAYS prefer text2cypher** for specific, targeted queries that mention specific entities by name
- **ALWAYS prefer text2cypher** for questions about specific dependencies, files, classes, methods, or developers
- **ALWAYS prefer text2cypher** for security questions about specific dependencies (e.g., "What CVEs affect X?")
- **Use predefined tools** only for broad overview questions without specific entities
- The LLM should be the only mechanism for tool selection - no keyword fallbacks are used

**DECISION RULE:** If the user mentions ANY specific name (dependency, file, class, method, developer), use text2cypher.

Be intelligent and contextual. Understand the user's intent and select the most appropriate tool(s)."""

            messages = [
                {
                    "role": "user",
                    "content": f"User Query: {user_query}\n\nPlease analyze this query and select appropriate tools.",
                }
            ]

            # Capture the LLM reasoning process
            llm_reasoning = {
                "prompt_sent": system_prompt.format(
                    tools_description=tools_description
                ),
                "user_message": f"User Query: {user_query}\n\nPlease analyze this query and select appropriate tools.",
                "llm_model": "gpt-4o",
                "temperature": 0.3,
                "max_tokens": 1000,
            }

            response = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt.format(tools_description=tools_description),
                temperature=0.3,  # Lower temperature for more consistent reasoning
                max_tokens=1000,
            )

            # Add the raw LLM response to reasoning and metrics
            llm_reasoning["raw_response"] = response
            if self.last_metrics:
                llm_reasoning["metrics"] = self.last_metrics

            # Debug logging
            logger.info(f"LLM Response for query '{user_query}': {response[:200]}...")

            # Parse the JSON response robustly
            import json
            import re

            try:
                cleaned_response = response.strip()
                # Remove common markdown code fences if present
                if cleaned_response.startswith("```"):
                    cleaned_response = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_response)
                    cleaned_response = re.sub(r"```$", "", cleaned_response).strip()
                # Extract the first balanced JSON object if extra text exists
                if not cleaned_response.startswith("{"):
                    start = cleaned_response.find("{")
                    end = cleaned_response.rfind("}")
                    if start != -1 and end != -1 and end > start:
                        cleaned_response = cleaned_response[start : end + 1]
                result = json.loads(cleaned_response)
                return {
                    "understanding": result.get("understanding", ""),
                    "selected_tools": result.get("selected_tools", []),
                    "reasoning": result.get("reasoning", ""),
                    "query_type": result.get("query_type", "general"),
                    "expected_insights": result.get("expected_insights", ""),
                    "llm_analysis": result.get("llm_analysis", ""),
                    "llm_reasoning_details": llm_reasoning,
                    "intelligence_level": "LLM-powered",
                }
            except json.JSONDecodeError as e:
                logger.warning(f"LLM response not in JSON format: {e}")
                logger.warning(f"Raw response: {response[:200]}...")
                return {
                    "understanding": "Failed to parse LLM response",
                    "selected_tools": [],
                    "reasoning": "JSON parsing error",
                    "query_type": "error",
                    "expected_insights": "Unable to determine",
                    "llm_analysis": f"JSON parsing error: {e}",
                }

        except Exception as e:
            logger.error(f"Error in LLM tool selection: {e}")
            return {
                "understanding": f"Error in LLM tool selection: {e}",
                "selected_tools": [],
                "reasoning": "Exception occurred during analysis",
                "query_type": "error",
                "expected_insights": "Unable to determine",
                "llm_analysis": f"Exception: {e}",
            }

    async def generate_intelligent_response(
        self,
        user_query: str,
        tool_results: List[Dict[str, Any]],
        query_type: str,
        expected_insights: str,
    ) -> Dict[str, Any]:
        """Generate an intelligent, contextual response based on query type and results."""
        if not self.client:
            basic_response = self._generate_basic_response(user_query, tool_results)
            return {
                "response": basic_response,
                "llm_reasoning": {
                    "intelligence_level": "fallback",
                    "reason": "LLM not available, using basic response generation",
                },
            }

        try:
            # Prepare context from tool results
            context = self._prepare_tool_results_context(tool_results)
            
            # Check if text2cypher was used
            text2cypher_used = any(result.get("tool_name") == "text2cypher" for result in tool_results)

            system_prompt = f"""You are an expert code analysis agent specializing in {query_type} analysis. 

QUERY TYPE: {query_type}
EXPECTED INSIGHTS: {expected_insights}

RESPONSE GUIDELINES:
1. **Be Contextual**: Tailor your response to the specific query type
2. **Provide Actionable Insights**: Don't just report data, explain what it means
3. **Prioritize by Impact**: Focus on the most important findings first
4. **Use Specific Examples**: Reference actual files, methods, and numbers
5. **Suggest Next Steps**: What should the user do with this information?

RESPONSE STRUCTURE:
- **Results Summary**: Key findings and metrics
- **Detailed Results**: Complete table with ALL results (no truncation)
- **Insights**: What the results mean
- **Recommendations**: Actionable next steps

IMPORTANT: Always show ALL results in the Detailed Results section. Do not truncate or limit the results to 5 items. If there are many results, format them in a proper table with all data visible.

{"SPECIAL INSTRUCTIONS FOR TEXT2CYPHER RESULTS:" if text2cypher_used else ""}
{"- Prominently display the generated Cypher query" if text2cypher_used else ""}
{"- Show the query explanation and results clearly" if text2cypher_used else ""}
{"- Format the results in a readable table or list" if text2cypher_used else ""}
{"- Include the query in a code block for easy copying" if text2cypher_used else ""}
{"- DO NOT show any Cypher queries for pre-built tools" if not text2cypher_used else ""}

Be professional, insightful, and actionable. Use the actual data provided."""

            messages = [
                {
                    "role": "user",
                    "content": f"User Query: {user_query}\n\nTool Results:\n{context}\n\nGenerate a comprehensive, intelligent response.",
                }
            ]

            # Capture LLM reasoning details
            llm_reasoning = {
                "prompt_sent": system_prompt,
                "user_message": f"User Query: {user_query}\n\nTool Results:\n{context}\n\nGenerate a comprehensive, intelligent response.",
                "llm_model": "gpt-4o",
                "temperature": 0.4,
                "max_tokens": 2500,
                "query_type": query_type,
                "expected_insights": expected_insights,
                "tool_results_summary": {
                    "total_tools": len(tool_results),
                    "total_results": sum(
                        r.get("result_count", 0) for r in tool_results
                    ),
                    "tools_used": [r.get("tool_name", "unknown") for r in tool_results],
                },
            }

            response = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=2500,
            )

            llm_reasoning["raw_response"] = response
            llm_reasoning["intelligence_level"] = "LLM-powered"
            if self.last_metrics:
                llm_reasoning["metrics"] = self.last_metrics

            # Minor post-formatting: ensure markdown headings and spacing are clean
            pretty = response.replace("\r\n", "\n")
            pretty = re.sub(r"\n{3,}", "\n\n", pretty)
            return {"response": pretty, "llm_reasoning": llm_reasoning}

        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            basic_response = self._generate_basic_response(user_query, tool_results)
            return {
                "response": basic_response,
                "llm_reasoning": {
                    "intelligence_level": "error",
                    "error": str(e),
                    "reason": "LLM response generation failed, using fallback",
                },
            }

    def _prepare_tool_results_context(self, tool_results: List[Dict[str, Any]]) -> str:
        """Prepare tool results in a format suitable for LLM consumption."""
        if not tool_results:
            return "No tool results available."

        context_parts = []
        for result in tool_results:
            if "error" in result:
                context_parts.append(
                    f"❌ Tool {result['tool_name']}: Error - {result['error']}"
                )
                continue

            context_parts.append(f"🔧 Tool: {result['tool_name']}")
            context_parts.append(f"📊 Category: {result['category']}")
            context_parts.append(f"📈 Results: {result['result_count']} items")

            # Special handling for text2cypher results
            if result.get("tool_name") == "text2cypher":
                if result.get("generated_query"):
                    context_parts.append(f"🔍 Generated Cypher Query:")
                    context_parts.append(f"  {result['generated_query']}")
                if result.get("explanation"):
                    context_parts.append(f"💡 Explanation: {result['explanation']}")

            # Add all results (no limitation for any tool)
            if result.get("results"):
                context_parts.append("📋 All Results:")
                for i, item in enumerate(result["results"]):
                    if isinstance(item, dict):
                        # Format dictionary items nicely
                        formatted_item = ", ".join(
                            [f"{k}: {v}" for k, v in item.items() if v]
                        )
                        context_parts.append(f"  {i+1}. {formatted_item}")
                    else:
                        context_parts.append(f"  {i+1}. {item}")

            context_parts.append("")

        return "\n".join(context_parts)

    def _generate_basic_response(
        self, user_query: str, tool_results: List[Dict[str, Any]]
    ) -> str:
        """Generate a basic response when LLM is not available."""
        if not tool_results:
            return f"I couldn't find any relevant information for your query: '{user_query}'. Please try rephrasing your question or check if the appropriate tools are available."

        response_parts = [f"Here are the results for your query: '{user_query}'\n"]

        for result in tool_results:
            if "error" in result:
                response_parts.append(
                    f"❌ {result['tool_name']}: Error - {result['error']}"
                )
                continue

            response_parts.append(f"🔧 {result['tool_name']} ({result['category']}):")
            response_parts.append(f"📊 Found {result['result_count']} results")

            if result.get("results"):
                response_parts.append("📋 Key findings:")
                for i, item in enumerate(result["results"][:3]):
                    if isinstance(item, dict):
                        formatted_item = ", ".join(
                            [f"{k}: {v}" for k, v in item.items() if v]
                        )
                        response_parts.append(f"  • {formatted_item}")
                    else:
                        response_parts.append(f"  • {item}")

            response_parts.append("")

        return "\n".join(response_parts)



    def _format_tools_for_llm(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools list for LLM consumption."""
        formatted = []
        for tool in tools:
            formatted.append(
                f"- {tool['name']} ({tool['category']}): {tool['description']}"
            )
        return "\n".join(formatted)


# Global LLM client
llm_client = AzureOpenAIClient()

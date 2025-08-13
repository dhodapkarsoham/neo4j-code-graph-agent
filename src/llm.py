"""Azure OpenAI LLM client for the agent."""

import logging
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from src.config import settings
import re
import time

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Azure OpenAI client for LLM interactions."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Azure OpenAI client."""
        logger.info(f"Azure OpenAI API Key: {'Set' if settings.azure_openai_api_key else 'Not set'}")
        logger.info(f"Azure OpenAI Endpoint: {'Set' if settings.azure_openai_endpoint else 'Not set'}")
        logger.info(f"Azure OpenAI Deployment: {'Set' if settings.azure_openai_deployment_name else 'Not set'}")
        
        if not all([
            settings.azure_openai_api_key,
            settings.azure_openai_endpoint,
            settings.azure_openai_deployment_name
        ]):
            logger.warning("Azure OpenAI configuration incomplete")
            return
        
        try:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            logger.info("✅ Azure OpenAI client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Azure OpenAI client: {e}")
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if the client is properly configured."""
        return self.client is not None
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
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
                max_tokens=max_tokens
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

            # Estimate cost (best-effort)
            model_name = settings.azure_openai_deployment_name or "unknown"
            cost_estimate = self._estimate_cost_usd(model_name, prompt_tokens, completion_tokens)

            logger.info(
                "LLM metrics | model=%s latency_ms=%.1f prompt_tokens=%s completion_tokens=%s total_tokens=%s estimated_cost_usd=%s",
                model_name,
                latency_ms,
                str(prompt_tokens) if prompt_tokens is not None else "?",
                str(completion_tokens) if completion_tokens is not None else "?",
                str(total_tokens) if total_tokens is not None else "?",
                f"{cost_estimate:.6f}" if cost_estimate is not None else "?",
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise

    def _estimate_cost_usd(self, model: str, prompt_tokens: Optional[int], completion_tokens: Optional[int]) -> Optional[float]:
        """Best-effort cost estimate in USD based on static pricing table.
        If tokens are missing or model unknown, returns None.
        NOTE: These are approximate and may not reflect your negotiated pricing.
        """
        if prompt_tokens is None and completion_tokens is None:
            return None
        # Prices per 1K tokens (approx; update as needed)
        pricing_per_1k = {
            # Common mappings; adjust to your Azure deployments
            "gpt-4o": {"input": 5.00, "output": 15.00},
            "gpt-4o-mini": {"input": 0.150, "output": 0.600},
            "gpt-4-turbo": {"input": 10.00, "output": 30.00},
            "gpt-4": {"input": 30.00, "output": 60.00},
            "gpt-35-turbo": {"input": 0.50, "output": 1.50},
        }
        # Normalize lookup by containment (deployment names often prefix the base model)
        base = None
        lower = model.lower()
        for key in pricing_per_1k.keys():
            if key in lower:
                base = key
                break
        if base is None:
            return None
        prices = pricing_per_1k[base]
        p = (prompt_tokens or 0) / 1000.0 * prices["input"]
        c = (completion_tokens or 0) / 1000.0 * prices["output"]
        return p + c

    async def analyze_query_and_select_tools(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user query and select appropriate tools using LLM intelligence."""
        logger.info(f"Analyzing query: '{user_query}' with {len(available_tools)} available tools")
        
        if not self.client:
            logger.warning("LLM client not available, using fallback")
            # Fallback to keyword-based approach if LLM not available
            return self._fallback_keyword_selection(user_query, available_tools)
        
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

RESPONSE FORMAT (JSON):
{{
    "understanding": "Brief explanation of what the user is asking for",
    "selected_tools": ["tool_name_1", "tool_name_2"],
    "reasoning": "Detailed explanation of why these tools were selected",
    "query_type": "security|quality|team|architecture|general",
    "expected_insights": "What kind of insights these tools should provide",
    "llm_analysis": "Step-by-step analysis of how you arrived at this decision"
}}

EXAMPLES:
- "Find security vulnerabilities" → security tools (vulnerable_dependencies_summary, cve_impact_analysis)
- "Which files are too complex?" → quality tools (complex_methods_analysis, large_files_analysis)
- "Who works on this module?" → team tools (developer_activity_summary, file_ownership_analysis)
- "Show me architectural issues" → architecture tools (architectural_bottlenecks, co_changed_files_analysis)

Be intelligent and contextual. Don't just match keywords - understand the intent."""

            messages = [
                {
                    "role": "user", 
                    "content": f"User Query: {user_query}\n\nPlease analyze this query and select appropriate tools."
                }
            ]
            
            # Capture the LLM reasoning process
            llm_reasoning = {
                "prompt_sent": system_prompt.format(tools_description=tools_description),
                "user_message": f"User Query: {user_query}\n\nPlease analyze this query and select appropriate tools.",
                "llm_model": "gpt-4o",
                "temperature": 0.3,
                "max_tokens": 1000
            }
            
            response = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt.format(tools_description=tools_description),
                temperature=0.3,  # Lower temperature for more consistent reasoning
                max_tokens=1000
            )
            
            # Add the raw LLM response to reasoning
            llm_reasoning["raw_response"] = response
            
            # Debug logging
            logger.info(f"LLM Response for query '{user_query}': {response[:200]}...")
            
            # Parse the JSON response robustly
            import json, re
            try:
                cleaned_response = response.strip()
                # Remove common markdown code fences if present
                if cleaned_response.startswith("```"):
                    cleaned_response = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_response)
                    cleaned_response = re.sub(r"```$", "", cleaned_response).strip()
                # Extract the first balanced JSON object if extra text exists
                if not cleaned_response.startswith('{'):
                    start = cleaned_response.find('{')
                    end = cleaned_response.rfind('}')
                    if start != -1 and end != -1 and end > start:
                        cleaned_response = cleaned_response[start:end+1]
                result = json.loads(cleaned_response)
                return {
                    "understanding": result.get("understanding", ""),
                    "selected_tools": result.get("selected_tools", []),
                    "reasoning": result.get("reasoning", ""),
                    "query_type": result.get("query_type", "general"),
                    "expected_insights": result.get("expected_insights", ""),
                    "llm_analysis": result.get("llm_analysis", ""),
                    "llm_reasoning_details": llm_reasoning,
                    "intelligence_level": "LLM-powered"
                }
            except json.JSONDecodeError as e:
                logger.warning(f"LLM response not in JSON format: {e}")
                logger.warning(f"Raw response: {response[:200]}...")
                logger.warning("Falling back to keyword selection due to JSON parsing error")
                return self._fallback_keyword_selection(user_query, available_tools)
                
        except Exception as e:
            logger.error(f"Error in LLM tool selection: {e}")
            logger.warning("Falling back to keyword selection due to exception")
            return self._fallback_keyword_selection(user_query, available_tools)
    
    async def generate_intelligent_response(
        self,
        user_query: str,
        tool_results: List[Dict[str, Any]],
        query_type: str,
        expected_insights: str
    ) -> Dict[str, Any]:
        """Generate an intelligent, contextual response based on query type and results."""
        if not self.client:
            basic_response = self._generate_basic_response(user_query, tool_results)
            return {
                "response": basic_response,
                "llm_reasoning": {
                    "intelligence_level": "fallback",
                    "reason": "LLM not available, using basic response generation"
                }
            }
        
        try:
            # Prepare context from tool results
            context = self._prepare_tool_results_context(tool_results)
            
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
- **Executive Summary**: 2-3 key findings
- **Detailed Analysis**: Specific examples and metrics
- **Risk Assessment**: What are the implications?
- **Recommendations**: Actionable next steps
- **Technical Details**: Specific technical findings

Be professional, insightful, and actionable. Use the actual data provided."""

            messages = [
                {
                    "role": "user",
                    "content": f"User Query: {user_query}\n\nTool Results:\n{context}\n\nGenerate a comprehensive, intelligent response."
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
                    "total_results": sum(r.get("result_count", 0) for r in tool_results),
                    "tools_used": [r.get("tool_name", "unknown") for r in tool_results]
                }
            }
            
            response = await self.generate_response(
                messages=messages,
                system_prompt=system_prompt,
                temperature=0.4,
                max_tokens=2500
            )
            
            llm_reasoning["raw_response"] = response
            llm_reasoning["intelligence_level"] = "LLM-powered"
            
            # Minor post-formatting: ensure markdown headings and spacing are clean
            pretty = response.replace('\r\n', '\n')
            pretty = re.sub(r"\n{3,}", "\n\n", pretty)
            return {
                "response": pretty,
                "llm_reasoning": llm_reasoning
            }
            
        except Exception as e:
            logger.error(f"Error generating intelligent response: {e}")
            basic_response = self._generate_basic_response(user_query, tool_results)
            return {
                "response": basic_response,
                "llm_reasoning": {
                    "intelligence_level": "error",
                    "error": str(e),
                    "reason": "LLM response generation failed, using fallback"
                }
            }
    
    def _prepare_tool_results_context(self, tool_results: List[Dict[str, Any]]) -> str:
        """Prepare tool results in a format suitable for LLM consumption."""
        if not tool_results:
            return "No tool results available."
        
        context_parts = []
        for result in tool_results:
            if "error" in result:
                context_parts.append(f"❌ Tool {result['tool_name']}: Error - {result['error']}")
                continue
            
            context_parts.append(f"🔧 Tool: {result['tool_name']}")
            context_parts.append(f"📊 Category: {result['category']}")
            context_parts.append(f"📈 Results: {result['result_count']} items")
            
            # Add sample results (first 3-5 items)
            if result.get('results'):
                context_parts.append("📋 Sample Results:")
                for i, item in enumerate(result['results'][:5]):
                    if isinstance(item, dict):
                        # Format dictionary items nicely
                        formatted_item = ", ".join([f"{k}: {v}" for k, v in item.items() if v])
                        context_parts.append(f"  {i+1}. {formatted_item}")
                    else:
                        context_parts.append(f"  {i+1}. {item}")
                
                if len(result['results']) > 5:
                    context_parts.append(f"  ... and {len(result['results']) - 5} more results")
            
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _generate_basic_response(self, user_query: str, tool_results: List[Dict[str, Any]]) -> str:
        """Generate a basic response when LLM is not available."""
        if not tool_results:
            return f"I couldn't find any relevant information for your query: '{user_query}'. Please try rephrasing your question or check if the appropriate tools are available."
        
        response_parts = [f"Here are the results for your query: '{user_query}'\n"]
        
        for result in tool_results:
            if "error" in result:
                response_parts.append(f"❌ {result['tool_name']}: Error - {result['error']}")
                continue
            
            response_parts.append(f"🔧 {result['tool_name']} ({result['category']}):")
            response_parts.append(f"📊 Found {result['result_count']} results")
            
            if result.get('results'):
                response_parts.append("📋 Key findings:")
                for i, item in enumerate(result['results'][:3]):
                    if isinstance(item, dict):
                        formatted_item = ", ".join([f"{k}: {v}" for k, v in item.items() if v])
                        response_parts.append(f"  • {formatted_item}")
                    else:
                        response_parts.append(f"  • {item}")
            
            response_parts.append("")
        
        return "\n".join(response_parts)
    
    def _fallback_keyword_selection(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback to keyword-based tool selection when LLM is not available."""
        query_lower = user_query.lower()
        available_tool_names = [tool["name"] for tool in available_tools]
        selected_tools = []
        
        # Keyword-based tool selection
        if any(word in query_lower for word in ["vulnerable", "dependency", "security", "cve"]):
            # Security-related tools
            security_tools = ["vulnerable_dependencies_summary", "cve_impact_analysis", "dependency_license_audit", "find_customer_facing_vulnerable_apis"]
            for tool in security_tools:
                if tool in available_tool_names:
                    selected_tools.append(tool)
        
        elif any(word in query_lower for word in ["complex", "refactor", "technical debt", "bottleneck"]):
            # Quality/Architecture tools
            quality_tools = ["complex_methods_analysis", "refactoring_priority_matrix", "architectural_bottlenecks", "large_files_analysis"]
            for tool in quality_tools:
                if tool in available_tool_names:
                    selected_tools.append(tool)
        
        elif any(word in query_lower for word in ["developer", "team", "activity", "ownership"]):
            # Team-related tools
            team_tools = ["developer_activity_summary", "file_ownership_analysis", "find_module_experts"]
            for tool in team_tools:
                if tool in available_tool_names:
                    selected_tools.append(tool)
        
        elif any(word in query_lower for word in ["architecture", "co-change", "module"]):
            # Architecture tools
            arch_tools = ["co_changed_files_analysis", "architectural_bottlenecks", "refactoring_priority_matrix"]
            for tool in arch_tools:
                if tool in available_tool_names:
                    selected_tools.append(tool)
        
        # If no tools selected, default to security tools for vulnerability queries
        if not selected_tools:
            if any(word in query_lower for word in ["vulnerable", "dependency", "security"]):
                if "vulnerable_dependencies_summary" in available_tool_names:
                    selected_tools.append("vulnerable_dependencies_summary")
            elif "complex" in query_lower:
                if "complex_methods_analysis" in available_tool_names:
                    selected_tools.append("complex_methods_analysis")
            elif "developer" in query_lower:
                if "developer_activity_summary" in available_tool_names:
                    selected_tools.append("developer_activity_summary")
        
        # Create understanding based on selected tools
        if selected_tools:
            understanding = f"User is asking about {query_lower.split()[0]} and related topics. Selected {len(selected_tools)} relevant tools."
            reasoning = f"Selected tools based on keywords: {', '.join(selected_tools)}"
        else:
            understanding = f"Could not determine specific tools for query: {user_query}"
            reasoning = "No specific keywords matched available tools"
        
        return {
            "understanding": understanding,
            "selected_tools": selected_tools,
            "reasoning": reasoning,
            "query_type": "fallback",
            "expected_insights": "Basic analysis based on keyword matching"
        }
    
    def _format_tools_for_llm(self, tools: List[Dict[str, Any]]) -> str:
        """Format tools list for LLM consumption."""
        formatted = []
        for tool in tools:
            formatted.append(f"- {tool['name']} ({tool['category']}): {tool['description']}")
        return "\n".join(formatted)


# Global LLM client
llm_client = AzureOpenAIClient()

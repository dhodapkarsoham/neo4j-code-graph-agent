"""
Integrated Text2Cypher implementation using LangGraph workflow.
Provides robust multi-step validation and error correction.
"""

import logging
from typing import TypedDict, Literal, Any, List
from langgraph.graph import StateGraph, END

from src.database import db
from src.llm import llm_client
from src.tools import schema_cache_manager

logger = logging.getLogger(__name__)

# State definition for the workflow
class Text2CypherState(TypedDict):
    question: str
    cypher_statement: str
    cypher_errors: List[str]
    database_records: Any
    next_action: Literal["generate_cypher", "correct_cypher", "execute_cypher", "end"]
    steps: List[str]
    generated_query: str
    explanation: str

# Input/Output state definitions
class InputState(TypedDict):
    question: str

class OutputState(TypedDict):
    answer: str
    steps: List[str]
    cypher_statement: str
    generated_query: str
    explanation: str

# Constants
NO_RESULTS = "I couldn't find any relevant information in the database"

async def guardrails(state: Text2CypherState) -> Text2CypherState:
    """
    Check if the question is relevant to our codebase domain.
    """
    try:
        guardrails_prompt = """You are a guardrail system for a code analysis tool. 
        Determine if the user's question is related to code analysis, software development, 
        or technical queries that can be answered using a code graph database.
        
        Return 'code' if the question is relevant to code analysis, software development, 
        or technical queries. Return 'other' for anything else.
        
        Examples of relevant questions:
        - Questions about code, methods, classes, files
        - Questions about dependencies, vulnerabilities, security
        - Questions about code quality, complexity, architecture
        - Questions about developers, teams, code ownership
        - Questions about CVEs, licenses, technical debt
        
        Examples of irrelevant questions:
        - Weather, news, general knowledge
        - Personal questions, entertainment
        - Questions not related to software development
        
        Question: {question}
        
        Is this question related to code analysis? (code/other):"""
        
        messages = [{"role": "user", "content": guardrails_prompt.format(question=state["question"])}]
        result = await llm_client.generate_response(messages)
        is_relevant = "code" in result.lower()
        
        return {
            **state,
            "next_action": "generate_cypher",  # Always proceed for now
            "steps": state.get("steps", []) + ["guardrails"]
        }
    except Exception as e:
        logger.error(f"Error in guardrails: {e}")
        logger.error(f"State keys: {list(state.keys())}")
        logger.error(f"State question: {state.get('question', 'NOT_FOUND')}")
        # Return a safe state even if guardrails fails
        return {
            **state,
            "next_action": "generate_cypher",
            "steps": state.get("steps", []) + ["guardrails_error"]
        }

async def generate_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Generate Cypher query from natural language question with dynamic schema validation.
    """
    logger.info("=== ENTERING generate_cypher function ===")
    logger.info(f"Input state type: {type(state)}")
    logger.info(f"Input state keys: {list(state.keys()) if isinstance(state, dict) else 'NOT_DICT'}")
    logger.info(f"Question: {state.get('question', 'NO_QUESTION') if isinstance(state, dict) else 'STATE_NOT_DICT'}")
    
    try:
        # Get the current schema
        logger.info("Fetching database schema...")
        schema_context = await schema_cache_manager.get_schema()
        logger.info(f"Schema fetched, length: {len(schema_context)} characters")
        logger.info(f"Schema preview (first 500 chars): {schema_context[:500]}")
        
        # Get schema rules for Cypher generation
        logger.info("Getting schema rules...")
        dynamic_rules = get_schema_rules()
        logger.info(f"Schema rules length: {len(dynamic_rules)} characters")
        
        logger.info("Building prompt template...")
        try:
            # Use .format() with named placeholders to avoid f-string conflicts with schema braces
            generate_prompt_template = """You are an expert Neo4j Cypher query generator for a code analysis graph database. 
            Your task is to generate ACCURATE and VALID Cypher queries that strictly adhere to the database schema.

            DATABASE SCHEMA:
            {schema_context}

            {dynamic_rules}

            IMPORTANT: For complex questions that ask multiple things (like "Which files have most versions? Are there any CVEs impacting them?"), 
            you should generate a SINGLE comprehensive Cypher query that answers the entire question, not separate queries.
            
            For example:
            - Question: "Which files have most versions? Are there any CVEs impacting them?"
            - Answer: Generate a query that finds files with most versions AND checks for CVEs affecting those files in one query
            
            RESPONSE FORMAT: Return ONLY the Cypher query as plain text, no JSON, no markdown, no explanations.
            
            Question: {question}
            
            Cypher query:"""
            
            generate_prompt = generate_prompt_template.format(
                schema_context=schema_context,
                dynamic_rules=dynamic_rules,
                question=state["question"]
            )
            logger.info("Prompt template built successfully")
        except Exception as prompt_error:
            logger.error(f"Error building prompt template: {prompt_error}")
            logger.error(f"schema_context type: {type(schema_context)}")
            logger.error(f"dynamic_rules type: {type(dynamic_rules)}")
            logger.error(f"question: {state.get('question', 'NO_QUESTION')}")
            raise
        
        logger.info("Creating messages...")
        try:
            messages = [{"role": "user", "content": generate_prompt}]
            logger.info("Messages created successfully")
        except Exception as format_error:
            logger.error(f"Error creating messages: {format_error}")
            raise
        
        logger.info(f"Final prompt length: {len(messages[0]['content'])} characters")
        logger.info(f"Final prompt preview (first 1000 chars): {messages[0]['content'][:1000]}")
        logger.info(f"Generating Cypher for question: {state['question']}")
        logger.info(f"State keys before LLM call: {list(state.keys())}")
        
        try:
            cypher_query = await llm_client.generate_response(messages)
            logger.info(f"Raw LLM response type: {type(cypher_query)}")
            logger.info(f"Raw LLM response: {repr(cypher_query)}")
            
            # Handle different response formats
            if isinstance(cypher_query, dict):
                logger.info(f"LLM returned dict with keys: {list(cypher_query.keys())}")
                # Extract content from dict response
                if 'content' in cypher_query:
                    cypher_query = cypher_query['content']
                elif 'text' in cypher_query:
                    cypher_query = cypher_query['text']
                elif 'query' in cypher_query:
                    cypher_query = cypher_query['query']
                elif 'cypher' in cypher_query:
                    cypher_query = cypher_query['cypher']
                else:
                    logger.warning(f"Dict response doesn't contain expected keys: {list(cypher_query.keys())}")
                    # Try to convert to string
                    cypher_query = str(cypher_query)
            
            # Convert to string if not already
            if not isinstance(cypher_query, str):
                cypher_query = str(cypher_query)
                logger.info(f"Converted response to string: {repr(cypher_query)}")
            
            # Check if the response is JSON
            if cypher_query.strip().startswith('{'):
                try:
                    import json
                    json_response = json.loads(cypher_query)
                    logger.info(f"Detected JSON response: {json_response}")
                    # Extract the query from JSON if it exists
                    if 'query' in json_response:
                        cypher_query = json_response['query']
                        logger.info(f"Extracted query from JSON: {cypher_query}")
                    elif 'cypher' in json_response:
                        cypher_query = json_response['cypher']
                        logger.info(f"Extracted cypher from JSON: {cypher_query}")
                    elif 'content' in json_response:
                        cypher_query = json_response['content']
                        logger.info(f"Extracted content from JSON: {cypher_query}")
                    else:
                        logger.warning(f"JSON response doesn't contain expected keys: {list(json_response.keys())}")
                except json.JSONDecodeError:
                    logger.info("Response looks like JSON but failed to parse, treating as text")
                    
        except Exception as llm_error:
            logger.error(f"LLM call failed: {llm_error}")
            logger.error(f"LLM error type: {type(llm_error)}")
            import traceback
            logger.error(f"LLM error traceback: {traceback.format_exc()}")
            raise
        
        # Clean up the response (remove markdown formatting if present)
        try:
            logger.info("Starting response cleanup...")
            cypher_query = cypher_query.strip()
            logger.info(f"After strip: {repr(cypher_query)}")
            
            if cypher_query.startswith("```cypher"):
                logger.info("Removing ```cypher prefix...")
                cypher_query = cypher_query[9:]
                logger.info(f"After removing cypher prefix: {repr(cypher_query)}")
            
            if cypher_query.startswith("```"):
                logger.info("Removing ``` prefix...")
                cypher_query = cypher_query[3:]
                logger.info(f"After removing prefix: {repr(cypher_query)}")
            
            if cypher_query.endswith("```"):
                logger.info("Removing ``` suffix...")
                cypher_query = cypher_query[:-3]
                logger.info(f"After removing suffix: {repr(cypher_query)}")
            
            cypher_query = cypher_query.strip()
            logger.info(f"Final cleaned Cypher query: {repr(cypher_query)}")
        except Exception as cleanup_error:
            logger.error(f"Error during response cleanup: {cleanup_error}")
            logger.error(f"Cleanup error type: {type(cleanup_error)}")
            import traceback
            logger.error(f"Cleanup error traceback: {traceback.format_exc()}")
            raise
        
        try:
            logger.info("Creating return state...")
            logger.info(f"State keys before return: {list(state.keys())}")
            logger.info(f"Steps before return: {state.get('steps', [])}")
            
            return_state = {
                **state,
                "cypher_statement": cypher_query,
                "next_action": "validate_cypher",
                "steps": state.get("steps", []) + ["generate_cypher"]
            }
            
            logger.info(f"Return state keys: {list(return_state.keys())}")
            logger.info(f"Return state steps: {return_state.get('steps', [])}")
            
            return return_state
        except Exception as return_error:
            logger.error(f"Error creating return state: {return_error}")
            logger.error(f"Return error type: {type(return_error)}")
            logger.error(f"State keys: {list(state.keys())}")
            import traceback
            logger.error(f"Return error traceback: {traceback.format_exc()}")
            raise
    except Exception as e:
        logger.error(f"Error in generate_cypher: {e}")
        logger.error(f"State keys: {list(state.keys())}")
        logger.error(f"State question: {state.get('question', 'NOT_FOUND')}")
        raise

def validate_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Validate the generated Cypher query for syntax and basic structure correctness.
    """

    cypher_query = state["cypher_statement"]
    errors = []
    warnings = []
    
    # Basic syntax validation
    try:
        # Test the query with EXPLAIN to check syntax
        explain_query = f"EXPLAIN {cypher_query}"
        db.execute_query(explain_query)
    except Exception as e:
        errors.append(f"Syntax error: {str(e)}")
        # If syntax is broken, don't continue with other validation
        return {
            **state,
            "cypher_errors": errors,
            "next_action": "correct_cypher",
            "steps": state["steps"] + ["validate_cypher"]
        }
    
    # Basic structure validation
    if not cypher_query.strip():
        errors.append("Empty Cypher query")
    
    if not any(keyword in cypher_query.upper() for keyword in ["MATCH", "RETURN"]):
        errors.append("Query must contain MATCH and RETURN clauses")
    
    # Check for common query structure issues
    if "LIMIT" not in cypher_query.upper():
        warnings.append("Consider adding LIMIT clause to prevent large result sets")
    
    if "DISTINCT" not in cypher_query.upper() and "count(" in cypher_query.lower():
        warnings.append("Consider using DISTINCT to avoid duplicate results")
    
    if "ORDER BY" not in cypher_query.upper() and "RETURN" in cypher_query.upper():
        warnings.append("Consider adding ORDER BY for consistent result ordering")
    
    # Check for potential performance issues
    if cypher_query.count("MATCH") > 3:
        warnings.append("Query has many MATCH clauses - consider optimization")
    
    if "OPTIONAL MATCH" not in cypher_query and "WHERE" in cypher_query:
        warnings.append("Consider using OPTIONAL MATCH for nullable relationships")
    
    # Determine next action based on validation results
    if errors:
        next_action = "correct_cypher"
    else:
        next_action = "execute_cypher"
    
    # Add warnings to the state for informational purposes
    validation_result = {
        **state,
        "cypher_errors": errors,
        "cypher_warnings": warnings,
        "next_action": next_action,
        "steps": state["steps"] + ["validate_cypher"]
    }
    
    # Log validation results
    if errors:
        logger.warning(f"Cypher validation found {len(errors)} errors: {errors}")
    if warnings:
        logger.info(f"Cypher validation found {len(warnings)} warnings: {warnings}")
    
    return validation_result

async def correct_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Intelligently correct the Cypher query based on validation errors with dynamic schema guidance.
    """
    schema_context = await schema_cache_manager.get_schema()
    
    # Get correction rules for Cypher error correction
    dynamic_correction_rules = get_correction_rules()
    
    # Build detailed error analysis
    error_analysis = "\n".join([f"- {error}" for error in state.get("cypher_errors", [])])
    warning_analysis = "\n".join([f"- {warning}" for warning in state.get("cypher_warnings", [])])
    
    correct_prompt = f"""You are an expert Neo4j Cypher query generator fixing a query written by a junior developer. 
    You need to correct the Cypher statement based on the provided errors and warnings.
    
    CRITICAL: Return ONLY the corrected Cypher query. Do not wrap in backticks, code blocks, or any other formatting.
    Return the raw Cypher query only!

    DATABASE SCHEMA:
    {schema_context}

    {dynamic_correction_rules}

    The original question is:
    {{question}}

    The problematic Cypher statement is:
    {{cypher}}

    The validation errors found:
    {{errors}}

    The validation warnings found:
    {{warnings}}

    CORRECTED CYPHER STATEMENT:"""
    
    messages = [{"role": "user", "content": correct_prompt.format(
        question=state["question"],
        errors=error_analysis,
        warnings=warning_analysis,
        cypher=state["cypher_statement"]
    )}]
    corrected_cypher = await llm_client.generate_response(messages)
    
    # Clean up the response
    corrected_cypher = corrected_cypher.strip()
    if corrected_cypher.startswith("```cypher"):
        corrected_cypher = corrected_cypher[9:]
    if corrected_cypher.startswith("```"):
        corrected_cypher = corrected_cypher[3:]
    if corrected_cypher.endswith("```"):
        corrected_cypher = corrected_cypher[:-3]
    corrected_cypher = corrected_cypher.strip()
    
    # Log the correction
    logger.info(f"Corrected Cypher query: {corrected_cypher}")
    
    return {
        "cypher_statement": corrected_cypher,
        "next_action": "validate_cypher",
        "steps": state["steps"] + ["correct_cypher"],
        **state
    }

def execute_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Execute the validated Cypher query.
    """
    try:
        records = db.execute_query(state["cypher_statement"])
        database_records = records if records else NO_RESULTS
    except Exception as e:
        logger.error(f"Error executing Cypher query: {e}")
        database_records = f"Error executing query: {str(e)}"
    
    return {
        **state,
        "database_records": database_records,
        "next_action": "end",
        "steps": state["steps"] + ["execute_cypher"]
    }

async def generate_final_answer(state: Text2CypherState) -> OutputState:
    """
    Generate the final answer from the database results.
    """
    generate_answer_prompt = """You are a helpful code analysis assistant. 
    Use the database results to provide a clear, informative answer to the user's question.
    Focus on code analysis, dependencies, vulnerabilities, and software development topics.
    
    CRITICAL INSTRUCTIONS:
    - If the question asks about files with most versions AND CVEs, analyze both aspects
    - If results show files with version counts, mention which files have the most versions
    - If results show CVEs affecting those files, clearly state which CVEs impact which files
    - If no CVEs are found for files with versions, state that clearly
    - If the question was about CVEs and results show CVEs, state that the component is affected
    - The database relationships are definitive - trust them over content analysis
    
    SPECIFIC RULES FOR FILE VERSIONS + CVEs:
    - If results contain file paths and version counts, list the files with most versions
    - If results contain CVE IDs for those files, list which CVEs affect which files
    - If no CVEs are found for files with versions, say "No CVEs were found affecting these files"
    - Always provide specific file names and CVE IDs when available
    
    Use the following results retrieved from a code analysis database to provide
    a succinct, definitive answer to the user's question.

    Results: {results}
    Question: {question}

    Answer:"""
    
    messages = [{"role": "user", "content": generate_answer_prompt.format(
        question=state["question"],
        results=state["database_records"]
    )}]
    final_answer = await llm_client.generate_response(messages)
    
    return {
        "answer": final_answer,
        "steps": state["steps"] + ["generate_final_answer"],
        "cypher_statement": state["cypher_statement"],
        "generated_query": state["cypher_statement"],
        "explanation": "Generated Cypher query for this analysis"
    }

# Conditional edge functions
def guardrails_condition(state: Text2CypherState) -> Literal["generate_cypher", "generate_final_answer"]:
    if state.get("next_action") == "end":
        return "generate_final_answer"
    elif state.get("next_action") == "generate_cypher":
        return "generate_cypher"

def validate_cypher_condition(state: Text2CypherState) -> Literal["generate_final_answer", "correct_cypher", "execute_cypher"]:
    if state.get("next_action") == "end":
        return "generate_final_answer"
    elif state.get("next_action") == "correct_cypher":
        return "correct_cypher"
    elif state.get("next_action") == "execute_cypher":
        return "execute_cypher"

def create_text2cypher_workflow():
    """
    Create the LangGraph workflow for text2cypher.
    """
    workflow = StateGraph(Text2CypherState)
    
    # Add nodes
    workflow.add_node("guardrails", guardrails)
    workflow.add_node("generate_cypher", generate_cypher)
    workflow.add_node("validate_cypher", validate_cypher)
    workflow.add_node("correct_cypher", correct_cypher)
    workflow.add_node("execute_cypher", execute_cypher)
    workflow.add_node("generate_final_answer", generate_final_answer)
    
    # Add edges - use "guardrails" as the entry point
    workflow.set_entry_point("guardrails")
    workflow.add_conditional_edges(
        "guardrails",
        guardrails_condition,
        {
            "generate_cypher": "generate_cypher",
            "generate_final_answer": "generate_final_answer"
        }
    )
    workflow.add_edge("generate_cypher", "validate_cypher")
    workflow.add_conditional_edges(
        "validate_cypher",
        validate_cypher_condition,
        {
            "generate_final_answer": "generate_final_answer",
            "correct_cypher": "correct_cypher",
            "execute_cypher": "execute_cypher"
        }
    )
    workflow.add_edge("execute_cypher", "generate_final_answer")
    workflow.add_edge("correct_cypher", "validate_cypher")
    workflow.add_edge("generate_final_answer", END)
    
    return workflow.compile()

# Global workflow instance
_text2cypher_workflow = None

def get_text2cypher_workflow():
    """
    Get or create the text2cypher workflow instance.
    """
    global _text2cypher_workflow
    if _text2cypher_workflow is None:
        _text2cypher_workflow = create_text2cypher_workflow()
    return _text2cypher_workflow

async def text2cypher(query: str) -> dict:
    """
    Enhanced text2cypher function using LangGraph workflow.
    
    Args:
        query: Natural language question
        
    Returns:
        dict: Contains answer, steps, cypher_statement, generated_query, explanation
    """

    try:
        # For now, use a simplified approach that works with the current LangGraph version
        # Initialize state
        state = {
            "question": query,
            "cypher_statement": "",
            "cypher_errors": [],
            "database_records": None,
            "next_action": "generate_cypher",
            "steps": [],
            "generated_query": "",
            "explanation": ""
        }
        
        # Step 1: Guardrails
        state = await guardrails(state)
        
        # Step 2: Generate Cypher
        if state["next_action"] == "generate_cypher":
            try:
                state = await generate_cypher(state)
            except Exception as e:
                logger.error(f"Error in generate_cypher: {e}")
                state["next_action"] = "end"
                state["steps"].append("error")
        
        # Step 3: Validate Cypher
        if state["next_action"] == "validate_cypher":
            state = validate_cypher(state)
        
        # Step 4: Correct Cypher (if needed)
        if state["next_action"] == "correct_cypher":
            state = await correct_cypher(state)
            # Re-validate after correction
            state = validate_cypher(state)
        
        # Step 5: Execute Cypher
        if state["next_action"] == "execute_cypher":
            state = execute_cypher(state)
        
        # Step 6: Generate Final Answer
        if state["next_action"] == "end":
            result = await generate_final_answer(state)
        else:
            # If we didn't reach the end, generate a basic answer
            result = {
                "answer": "I processed your query but encountered some issues. Please try rephrasing your question.",
                "steps": state["steps"],
                "cypher_statement": state.get("cypher_statement", ""),
                "generated_query": state.get("cypher_statement", ""),
                "explanation": f"Workflow ended at step: {state.get('next_action', 'unknown')}"
            }
        
        return result
        
    except Exception as e:
        logger.error(f"Error in text2cypher: {e}")
        return {
            "answer": f"Sorry, I encountered an error processing your question: {str(e)}",
            "steps": ["error"],
            "cypher_statement": "",
            "generated_query": "",
            "explanation": f"Error: {str(e)}"
        }

def get_schema_rules() -> str:
    """
    Generate schema rules for Cypher generation prompts.
    """
    return """CRITICAL QUERY GENERATION RULES - YOU MUST FOLLOW THESE EXACTLY:

QUERY GENERATION RULES:
1. ALWAYS use exact node labels and relationship types from the schema above
2. ALWAYS use correct relationship direction (arrows show direction)
3. ALWAYS use exact property names from the schema above
4. ALWAYS include LIMIT clauses (typically 50-100) for large result sets
5. ALWAYS use DISTINCT to avoid duplicate results
6. ALWAYS include relevant properties in RETURN clause
7. ALWAYS use proper WHERE clauses for filtering
8. ALWAYS order results by relevant criteria (severity DESC, count DESC, etc.)
9. ALWAYS use OPTIONAL MATCH when relationships might not exist
10. NEVER invent node labels, relationships, or properties not in the schema above
11. CRITICAL: For File nodes, ALWAYS use f.path (not f.name) when filtering by filename or filepath
12. CRITICAL: Use CONTAINS for partial file name matches (e.g., f.path CONTAINS 'filename.java')

FEW-SHOT LEARNING EXAMPLES:

Example 1 - Security Analysis:
Question: 'Show me high severity CVEs affecting our dependencies'
Cypher: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency) WHERE cve.cvss_score >= 7.0 RETURN dep.name, cve.id, cve.cvss_score ORDER BY cve.cvss_score DESC LIMIT 50

Example 2 - Complex Methods:
Question: 'Find methods with more than 50 lines'
Cypher: MATCH (m:Method)<-[:DECLARES]-(f:File) WHERE m.estimated_lines > 50 RETURN f.path, m.name, m.estimated_lines ORDER BY m.estimated_lines DESC LIMIT 50

Example 2b - File-specific Query (IMPORTANT - Always use f.path for file matching):
Question: 'Which developers worked on GraphsTest.java?'
Cypher: MATCH (dev:Developer)-[:AUTHORED]->(c:Commit)-[:CHANGED]->(fv:FileVer)-[:OF_FILE]->(f:File) WHERE f.path CONTAINS 'GraphsTest.java' RETURN DISTINCT dev.name, dev.email ORDER BY dev.name LIMIT 50

Example 3 - Developer Activity:
Question: 'Who are the most active developers?'
Cypher: MATCH (dev:Developer)-[:AUTHORED]->(c:Commit) RETURN dev.name, count(c) as commits ORDER BY commits DESC LIMIT 50

Example 4 - Method Calls:
Question: 'Show me method call relationships'
Cypher: MATCH (m1:Method)-[:CALLS]->(m2:Method) RETURN m1.name, m2.name LIMIT 50

Example 5 - Large Files:
Question: 'Which files are too large?'
Cypher: MATCH (f:File) WHERE f.total_lines > 1000 RETURN f.path, f.total_lines ORDER BY f.total_lines DESC LIMIT 50


Example 6 - File Versions Query:
Question: 'Which files have most versions?'
Cypher: MATCH (fv:FileVer)-[:OF_FILE]->(f:File) RETURN f.path, count(fv) as version_count ORDER BY version_count DESC LIMIT 50

Example 7 - Complex Query (File Versions + CVEs):
Question: 'Which files have most versions? Are there any CVEs impacting them?'
Cypher: MATCH (fv:FileVer)-[:OF_FILE]->(f:File) WITH f, count(fv) as version_count ORDER BY version_count DESC LIMIT 10 OPTIONAL MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)<-[:DEPENDS_ON]-(imp:Import)<-[:IMPORTS]-(f) RETURN f.path, version_count, collect(DISTINCT cve.id) as affecting_cves ORDER BY version_count DESC

VALIDATION CHECKLIST (verify your query has):
✅ Correct node labels from the schema above
✅ Correct relationship types from the schema above
✅ Correct relationship direction (arrows point right way)
✅ Correct property names from the schema above
✅ LIMIT clause included
✅ DISTINCT used if needed
✅ Proper WHERE clauses
✅ Relevant properties in RETURN
✅ Logical ordering (ORDER BY)"""

def get_correction_rules() -> str:
    """
    Generate correction rules for Cypher error correction.
    """
    return """COMMON CORRECTION PATTERNS:
1. Node label errors: Replace invalid labels with correct ones from the schema above
2. Relationship errors: Use exact relationship types and correct direction from the schema above
3. Property errors: Use exact property names from the schema above
4. Missing LIMIT: Add "LIMIT 50" or "LIMIT 100" to prevent large results
5. Missing DISTINCT: Add "DISTINCT" before RETURN for unique results
6. Missing ORDER BY: Add "ORDER BY" for consistent sorting
7. Relationship direction: Ensure arrows point in correct semantic direction

EXAMPLE CORRECTIONS:
- Wrong: MATCH (f:file) RETURN f.path → Correct: MATCH (f:File) RETURN f.path
- Wrong: MATCH (cve:CVE)<-[:AFFECTS]-(dep:Dependency) → Correct: MATCH (cve:CVE)-[:AFFECTS]->(dep:ExternalDependency)
- Wrong: MATCH (m:Method) RETURN m.complexity → Correct: MATCH (m:Method) RETURN m.cyclomatic_complexity
- Wrong: MATCH (f:File) RETURN f.path → Correct: MATCH (f:File) RETURN f.path LIMIT 50
- Wrong: MATCH (cve:CVE) RETURN cve.id, cve.score → Correct: MATCH (cve:CVE) RETURN cve.id, cve.cvss_score ORDER BY cve.cvss_score DESC LIMIT 50
- Wrong: WHERE f.name = 'GraphsTest.java' → Correct: WHERE f.path CONTAINS 'GraphsTest.java'
- Wrong: WHERE f.name CONTAINS 'Test' → Correct: WHERE f.path CONTAINS 'Test'"""

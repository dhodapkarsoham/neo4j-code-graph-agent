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
        "next_action": "generate_cypher",  # Always proceed for now
        "steps": ["guardrails"],
        **state
    }

async def generate_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Generate Cypher query from natural language question.
    """

    # Get the current schema
    schema_context = await schema_cache_manager.get_schema()
    
    generate_prompt = """You are a Cypher expert for a code analysis graph database. 
    Generate Cypher queries to answer questions about code, dependencies, vulnerabilities, and software development.
    
    Database Schema:
    {schema}
    
    IMPORTANT RELATIONSHIP SEMANTICS:
    - AFFECTS: When a CVE AFFECTS an ExternalDependency, it means the CVE impacts that dependency
    - DEPENDS_ON: When an Import DEPENDS_ON an ExternalDependency, it means the code uses that dependency
    - CONTAINS_METHOD: When a Class CONTAINS_METHOD, it means the method belongs to that class
    - DEFINES: When a File DEFINES a Class/Method, it means the class/method is declared in that file
    - CALLS: When a Method CALLS another Method, it means there's a method invocation
    
    Guidelines:
    - Use proper Cypher syntax
    - Include LIMIT clauses for large result sets
    - Use parameterized queries when possible
    - Focus on code analysis, dependencies, CVEs, and software development
    - Return only the Cypher query, no explanations
    - When querying relationships, understand that the relationship direction indicates the semantic meaning
    
    Question: {question}
    
    Generate a Cypher query:"""
    
    messages = [{"role": "user", "content": generate_prompt.format(
        question=state["question"],
        schema=schema_context
    )}]
    cypher_query = await llm_client.generate_response(messages)
    
    # Clean up the response (remove markdown formatting if present)
    cypher_query = cypher_query.strip()
    if cypher_query.startswith("```cypher"):
        cypher_query = cypher_query[9:]
    if cypher_query.startswith("```"):
        cypher_query = cypher_query[3:]
    if cypher_query.endswith("```"):
        cypher_query = cypher_query[:-3]
    cypher_query = cypher_query.strip()
    
    return {
        **state,
        "cypher_statement": cypher_query,
        "next_action": "validate_cypher",
        "steps": state["steps"] + ["generate_cypher"]
    }

def validate_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Validate the generated Cypher query for syntax and schema correctness.
    """

    cypher_query = state["cypher_statement"]
    errors = []
    
    try:
        # Test the query with EXPLAIN to check syntax
        explain_query = f"EXPLAIN {cypher_query}"
        db.execute_query(explain_query)
        
        # Additional validation checks
        if not cypher_query.strip():
            errors.append("Empty Cypher query")
        
        # Check for basic Cypher patterns
        if not any(keyword in cypher_query.upper() for keyword in ["MATCH", "RETURN"]):
            errors.append("Query must contain MATCH and RETURN clauses")
            
    except Exception as e:
        errors.append(f"Syntax error: {str(e)}")
    
    # Determine next action based on validation results
    if errors:
        next_action = "correct_cypher"
    else:
        next_action = "execute_cypher"
    
    return {
        **state,
        "cypher_errors": errors,
        "next_action": next_action,
        "steps": state["steps"] + ["validate_cypher"]
    }

async def correct_cypher(state: Text2CypherState) -> Text2CypherState:
    """
    Correct the Cypher query based on validation errors.
    """
    schema_context = await schema_cache_manager.get_schema()
    
    correct_prompt = """You are a Cypher expert reviewing a statement written by a junior developer. 
    You need to correct the Cypher statement based on the provided errors. 
    Do not wrap the response in any backticks or anything else. 
    Respond with a Cypher statement only!
    
    Check for invalid syntax or semantics and return a corrected Cypher statement.

    Schema:
    {schema}

    The question is:
    {question}

    The Cypher statement is:
    {cypher}

    The errors are:
    {errors}

    Corrected Cypher statement:"""
    
    messages = [{"role": "user", "content": correct_prompt.format(
        question=state["question"],
        errors="\n".join(state["cypher_errors"]),
        cypher=state["cypher_statement"],
        schema=schema_context
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
    - If the question asks "What CVEs affect X" and the results show CVEs, then X IS affected by those CVEs
    - The database query used the AFFECTS relationship to find CVEs linked to the component
    - If results are found, the component IS affected by the listed CVEs
    - Do NOT say "no data found" or "no CVEs affect" when results are present
    - The database relationships are definitive - trust them over content analysis
    
    SPECIFIC RULES:
    - If results contain CVE IDs, descriptions, and scores, present them as affecting the component
    - If the question was about CVEs and results show CVEs, state that the component is affected
    - Never dismiss results based on CVE description content
    
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

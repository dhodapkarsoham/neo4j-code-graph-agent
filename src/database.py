"""Neo4j database connection and query management."""

import logging
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase
from src.config import settings
import time

logger = logging.getLogger(__name__)


class Neo4jDatabase:
    """Neo4j database connection and query manager."""
    
    def __init__(self):
        """Initialize database connection."""
        self.driver = None
        self.last_metrics: Optional[Dict[str, Any]] = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password)
            )
            # Test connection
            with self.driver.session(database=settings.neo4j_database) as session:
                session.run("RETURN 1")
            logger.info("✅ Connected to Neo4j database")
        except Exception as e:
            logger.error("❌ Failed to connect to Neo4j: Connection error occurred")
            self.driver = None
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.driver:
            raise ConnectionError("Not connected to Neo4j database")
        
        try:
            with self.driver.session(database=settings.neo4j_database) as session:
                start_time = time.perf_counter()
                result = session.run(query, parameters or {})
                records = [dict(record) for record in result]
                # Try to consume summary for timing metrics if available
                available_after_ms = None
                consumed_after_ms = None
                try:
                    summary = result.consume()
                    available_after_ms = getattr(summary, "result_available_after", None)
                    consumed_after_ms = getattr(summary, "result_consumed_after", None)
                except Exception:
                    pass
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                # Store metrics for callers
                self.last_metrics = {
                    "rows": len(records),
                    "latency_ms": latency_ms,
                    "available_after_ms": available_after_ms,
                    "consumed_after_ms": consumed_after_ms,
                }
                logger.info(
                    "Neo4j metrics | rows=%d latency_ms=%.1f available_after_ms=%s consumed_after_ms=%s",
                    len(records),
                    latency_ms,
                    str(available_after_ms) if available_after_ms is not None else "?",
                    str(consumed_after_ms) if consumed_after_ms is not None else "?",
                )
                return records
        except Exception as e:
            logger.error("Query execution failed: An error occurred during query execution")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            with self.driver.session(database=settings.neo4j_database) as session:
                result = session.run("RETURN 1 as test")
                return result.single()["test"] == 1
        except Exception:
            return False
    
    def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information."""
        query = """
        CALL db.schema.visualization()
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        try:
            result = self.execute_query(query)
            return result[0] if result else {"nodes": [], "relationships": []}
        except Exception as e:
            logger.warning(f"Could not get schema info: {e}")
            return {"nodes": [], "relationships": []}
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()


# Global database instance
db = Neo4jDatabase()

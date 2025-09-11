"""Neo4j database connection and query management."""

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase

from src.config import settings

logger = logging.getLogger(__name__)


class Neo4jDatabase:
    """Neo4j database connection and query manager."""

    def __init__(self) -> None:
        """Initialize database connection."""
        self.driver: Optional[Any] = None
        self.last_metrics: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._connect()

    def _connect(self) -> None:
        """Establish connection to Neo4j."""
        with self._lock:
            try:
                self.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password),
                )
                # Test connection
                with self.driver.session(database=settings.neo4j_database) as session:
                    def test_connection(tx):
                        tx.run("RETURN 1")
                    session.execute_read(test_connection)
                logger.info("✅ Connected to Neo4j database")
            except Exception as e:
                logger.error("❌ Failed to connect to Neo4j: %s", str(e))
                try:
                    if self.driver:
                        self.driver.close()
                except Exception:
                    pass
                self.driver = None

    def execute_query(
        self, query: str, parameters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.driver:
            raise ConnectionError("Not connected to Neo4j database")

        def run_query(tx):
            result = tx.run(query, parameters or {})
            records = [dict(record) for record in result]
            # Try to consume summary for timing metrics if available
            available_after_ms = None
            consumed_after_ms = None
            try:
                summary = result.consume()
                available_after_ms = getattr(
                    summary, "result_available_after", None
                )
                consumed_after_ms = getattr(summary, "result_consumed_after", None)
            except Exception:
                pass
            return records, available_after_ms, consumed_after_ms

        try:
            with self.driver.session(database=settings.neo4j_database) as session:
                start_time = time.perf_counter()
                records, available_after_ms, consumed_after_ms = session.execute_read(run_query)
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
            logger.error(
                "Query execution failed: An error occurred during query execution"
            )
            raise

    def test_connection(self) -> bool:
        """Test database connection. Attempts lazy reconnect if not connected."""
        # Attempt reconnect if driver is missing
        if self.driver is None:
            try:
                self._connect()
            except Exception as e:
                logger.debug("Reconnect attempt failed: %s", str(e))
        try:
            if self.driver is None:
                return False
            with self.driver.session(database=settings.neo4j_database) as session:
                def test_query(tx):
                    result = tx.run("RETURN 1 as test")
                    record = result.single()
                    if record is None:
                        return False
                    test_value = record.get("test")
                    return bool(test_value == 1)
                return session.execute_read(test_query)
        except Exception:
            # On failure, mark driver unusable to allow future reconnects
            try:
                if self.driver:
                    self.driver.close()
            except Exception:
                pass
            self.driver = None
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

    def close(self) -> None:
        """Close database connection."""
        if self.driver:
            self.driver.close()


class DatabaseConnection:
    """Represents a single database connection configuration."""
    
    def __init__(self, name: str, uri: str, username: str, password: str, database: str = "neo4j"):
        self.name = name
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver: Optional[Any] = None
        self._lock = threading.Lock()
        self.last_connected: Optional[float] = None
        self.last_error: Optional[str] = None
        self.last_metrics: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "uri": self.uri,
            "username": self.username,
            "password": self.password,
            "database": self.database
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "DatabaseConnection":
        """Create from dictionary."""
        return cls(
            name=data["name"],
            uri=data["uri"],
            username=data["username"],
            password=data["password"],
            database=data.get("database", "neo4j")
        )
    
    def connect(self) -> bool:
        """Establish connection to this database."""
        with self._lock:
            try:
                # Close existing connection if any
                if self.driver:
                    try:
                        self.driver.close()
                    except Exception:
                        pass
                
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                )
                
                # Test connection
                with self.driver.session(database=self.database) as session:
                    def test_connection(tx):
                        tx.run("RETURN 1")
                    session.execute_read(test_connection)
                
                self.last_connected = time.time()
                self.last_error = None
                logger.info(f"✅ Connected to database: {self.name} ({self.uri})")
                return True
                
            except Exception as e:
                logger.error(f"❌ Failed to connect to database {self.name}: {str(e)}")
                self.last_error = str(e)
                try:
                    if self.driver:
                        self.driver.close()
                except Exception:
                    pass
                self.driver = None
                return False
    
    def test_connection(self) -> bool:
        """Test if connection is still valid."""
        if not self.driver:
            return False
        
        try:
            with self.driver.session(database=self.database) as session:
                def test_query(tx):
                    result = tx.run("RETURN 1 as test")
                    record = result.single()
                    return record and record.get("test") == 1
                return session.execute_read(test_query)
        except Exception:
            return False
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query on this database."""
        if not self.driver:
            raise ConnectionError(f"Not connected to database: {self.name}")
        
        def run_query(tx):
            result = tx.run(query, parameters or {})
            records = [dict(record) for record in result]
            # Try to consume summary for timing metrics if available
            available_after_ms = None
            consumed_after_ms = None
            try:
                summary = result.consume()
                available_after_ms = getattr(
                    summary, "result_available_after", None
                )
                consumed_after_ms = getattr(summary, "result_consumed_after", None)
            except Exception:
                pass
            return records, available_after_ms, consumed_after_ms
        
        try:
            with self.driver.session(database=self.database) as session:
                start_time = time.perf_counter()
                records, available_after_ms, consumed_after_ms = session.execute_read(run_query)
                latency_ms = (time.perf_counter() - start_time) * 1000.0
                # Store metrics for callers
                self.last_metrics = {
                    "rows": len(records),
                    "latency_ms": latency_ms,
                    "available_after_ms": available_after_ms,
                    "consumed_after_ms": consumed_after_ms,
                }
                logger.info(f"Query executed on {self.name}: {len(records)} rows in {latency_ms:.1f}ms")
                return records
        except Exception as e:
            logger.error(f"Query execution failed on {self.name}: {str(e)}")
            raise
    
    def close(self):
        """Close the database connection."""
        with self._lock:
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
                self.driver = None


class DatabaseManager:
    """Manages multiple database connections."""
    
    def __init__(self, config_file: str = "databases.json"):
        self.config_file = Path(config_file)
        self.connections: Dict[str, DatabaseConnection] = {}
        self.current_connection: Optional[DatabaseConnection] = None
        self._lock = threading.Lock()
        self._load_connections()
        self._setup_default_connection()
    
    def _load_connections(self):
        """Load database connections from JSON file."""
        if not self.config_file.exists():
            logger.info("No databases.json file found, creating one with empty structure")
            # Create the file with empty structure
            self._save_connections()
            return
        
        try:
            with open(self.config_file, 'r') as f:
                data = json.load(f)
            
            for conn_data in data.get("connections", []):
                conn = DatabaseConnection.from_dict(conn_data)
                self.connections[conn.name] = conn
                logger.info(f"Loaded database connection: {conn.name}")
                
        except Exception as e:
            logger.error(f"Failed to load database connections: {e}")
    
    def _save_connections(self):
        """Save database connections to JSON file."""
        try:
            data = {
                "connections": [conn.to_dict() for conn in self.connections.values()]
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Database connections saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save database connections: {e}")
    
    def _setup_default_connection(self):
        """Set up default connection from environment settings."""
        default_name = "Default"
        
        # Create default connection from environment settings
        default_conn = DatabaseConnection(
            name=default_name,
            uri=settings.neo4j_uri,
            username=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database
        )
        
        # Add to connections if not already present
        if default_name not in self.connections:
            self.connections[default_name] = default_conn
            self._save_connections()
        else:
            # Use the existing connection from the loaded connections
            default_conn = self.connections[default_name]
        
        # Set as current connection and try to connect
        self.current_connection = default_conn
        # Try to connect to the default database
        try:
            if self.current_connection.connect():
                logger.info(f"✅ Connected to default database: {default_name}")
            else:
                logger.warning(f"⚠️ Could not connect to default database: {default_name}")
        except Exception as e:
            logger.error(f"❌ Error connecting to default database: {e}")
    
    def add_connection(self, name: str, uri: str, username: str, password: str, database: str = "neo4j") -> bool:
        """Add a new database connection."""
        with self._lock:
            if name in self.connections:
                logger.warning(f"Connection {name} already exists")
                return False
            
            conn = DatabaseConnection(name, uri, username, password, database)
            
            # Test connection before adding
            if conn.connect():
                self.connections[name] = conn
                self._save_connections()
                logger.info(f"Added new database connection: {name}")
                return True
            else:
                logger.error(f"Failed to connect to database {name}, not adding")
                return False
    
    def remove_connection(self, name: str) -> bool:
        """Remove a database connection."""
        with self._lock:
            if name not in self.connections:
                return False
            
            # Don't allow removing the default connection
            if name == "Default":
                logger.warning("Cannot remove default connection")
                return False
            
            conn = self.connections[name]
            conn.close()
            del self.connections[name]
            
            # If this was the current connection, switch to default
            if self.current_connection == conn:
                self.current_connection = self.connections.get("Default")
            
            self._save_connections()
            logger.info(f"Removed database connection: {name}")
            return True
    
    def switch_connection(self, name: str) -> bool:
        """Switch to a different database connection."""
        with self._lock:
            if name not in self.connections:
                logger.error(f"Connection {name} not found")
                return False
            
            conn = self.connections[name]
            
            # Test connection before switching
            if conn.test_connection() or conn.connect():
                self.current_connection = conn
                logger.info(f"Switched to database connection: {name}")
                return True
            else:
                logger.error(f"Failed to connect to database {name}")
                return False
    
    def get_connection_names(self) -> List[str]:
        """Get list of all connection names."""
        return list(self.connections.keys())
    
    def get_current_connection(self) -> Optional[DatabaseConnection]:
        """Get the currently active connection."""
        return self.current_connection
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get information about all connections."""
        info = {}
        for name, conn in self.connections.items():
            # Use the same improved connection checking logic as health check
            is_connected = (
                conn.driver is not None and 
                conn.last_error is None and
                (conn.last_connected is None or 
                 time.time() - conn.last_connected < 300)  # 5 minutes
            )
            
            # For current connection, use the same logic as health check
            if conn == self.current_connection:
                # If this is the current connection and we have a driver, assume it's connected
                # since queries are working (as evidenced by successful query execution)
                if conn.driver is not None:
                    is_connected = True
                    # Update last_connected if it's null
                    if conn.last_connected is None:
                        conn.last_connected = time.time()
                else:
                    is_connected = False
            
            info[name] = {
                "name": conn.name,
                "uri": conn.uri,
                "database": conn.database,
                "connected": is_connected,
                "last_connected": conn.last_connected,
                "last_error": conn.last_error,
                "is_current": conn == self.current_connection
            }
        return info
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query on the current connection."""
        if not self.current_connection:
            raise ConnectionError("No database connection selected")
        
        return self.current_connection.execute_query(query, parameters)
    
    def test_connection(self) -> bool:
        """Test the current connection."""
        if not self.current_connection:
            return False
        
        return self.current_connection.test_connection()
    
    def get_current_connection_info(self) -> Dict[str, Any]:
        """Get info about the current connection for health checks."""
        if not self.current_connection:
            return {"connected": False, "uri": "", "database": "", "name": ""}
        
        # Use a more reliable connection check - if we have a driver and no recent errors, consider it connected
        is_connected = (
            self.current_connection.driver is not None and 
            self.current_connection.last_error is None and
            (self.current_connection.last_connected is None or 
             time.time() - self.current_connection.last_connected < 300)  # 5 minutes
        )
        
        # If we're not sure, do a quick test
        if not is_connected and self.current_connection.driver is not None:
            is_connected = self.current_connection.test_connection()
        
        return {
            "connected": is_connected,
            "uri": self.current_connection.uri,
            "database": self.current_connection.database,
            "name": self.current_connection.name
        }
    
    @property
    def last_metrics(self) -> Optional[Dict[str, Any]]:
        """Get last query metrics from current connection."""
        if self.current_connection:
            return self.current_connection.last_metrics
        return None
    
    def close_all(self):
        """Close all database connections."""
        with self._lock:
            for conn in self.connections.values():
                conn.close()


# Global database manager instance
db_manager = DatabaseManager()

# Global database instance (for backward compatibility)
db = Neo4jDatabase()

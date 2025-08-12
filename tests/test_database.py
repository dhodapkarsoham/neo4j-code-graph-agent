"""Tests for database connection."""

import pytest
from unittest.mock import patch, MagicMock
from neo4j.exceptions import ServiceUnavailable, AuthError

from src.database import db

import logging

# Custom filter to suppress specific connection error messages
class SuppressConnectionErrors(logging.Filter):
    def filter(self, record):
        return 'Failed to write data to connection' not in record.getMessage()

# Apply the custom filter to the Neo4j logger
logging.getLogger('neo4j').addFilter(SuppressConnectionErrors())


class TestDatabaseConnection:
    """Test cases for database connection."""

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_connection_success(self, mock_session, mock_driver):
        """Test successful database connection."""
        mock_driver.return_value = MagicMock()
        
        # Test connection
        mock_driver.return_value.verify_connectivity.return_value = True
        
        # Test query execution
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        mock_result.data.return_value = [{"result": "test"}]
        
        # Test the connection
        result = db.execute_query("MATCH (n) RETURN n LIMIT 1")
        
        assert result == [{"result": "test"}]
        mock_driver.return_value.verify_connectivity.assert_called_once()
        mock_session.return_value.__enter__.return_value.run.assert_called_once_with("MATCH (n) RETURN n LIMIT 1", {})

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_connection_failure(self, mock_session, mock_driver):
        """Test database connection failure."""
        mock_driver.return_value = MagicMock()
        
        # Mock connection failure
        mock_driver.return_value.verify_connectivity.side_effect = ServiceUnavailable("Connection failed")
        
        with pytest.raises(ServiceUnavailable):
            db.execute_query("MATCH (n) RETURN n LIMIT 1")

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_authentication_failure(self, mock_session, mock_driver):
        """Test database authentication failure."""
        mock_driver.return_value = MagicMock()
        
        # Mock authentication failure
        mock_driver.return_value.verify_connectivity.side_effect = AuthError("Invalid credentials")
        
        with pytest.raises(AuthError):
            db.execute_query("MATCH (n) RETURN n LIMIT 1")

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_query_execution_with_parameters(self, mock_session, mock_driver):
        """Test query execution with parameters."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        mock_result.data.return_value = [{"name": "test_node"}]
        
        parameters = {"name": "test"}
        result = db.execute_query("MATCH (n {name: $name}) RETURN n", parameters)
        
        assert result == [{"name": "test_node"}]
        mock_session.return_value.__enter__.return_value.run.assert_called_once_with("MATCH (n {name: $name}) RETURN n", parameters)

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_query_execution_error(self, mock_session, mock_driver):
        """Test query execution with error."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        # Mock query execution error
        mock_session.return_value.__enter__.return_value.run.side_effect = Exception("Query syntax error")
        
        with pytest.raises(Exception, match="Query syntax error"):
            db.execute_query("INVALID QUERY")

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_connection_verification(self, mock_session, mock_driver):
        """Test connection verification."""
        mock_driver.return_value = MagicMock()
        
        # Test successful verification
        mock_driver.return_value.verify_connectivity.return_value = True
        
        # This should not raise an exception
        db.execute_query("MATCH (n) RETURN n LIMIT 1")
        
        mock_driver.return_value.verify_connectivity.assert_called_once()

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_session_management(self, mock_session, mock_driver):
        """Test proper session management."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_session.return_value.__exit__.return_value = None
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        mock_result.data.return_value = []
        
        db.execute_query("MATCH (n) RETURN n")
        
        # Verify session was created and closed properly
        mock_session.return_value.__enter__.assert_called_once()
        mock_session.return_value.__enter__.return_value.close.assert_called_once()

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_empty_result_handling(self, mock_session, mock_driver):
        """Test handling of empty query results."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        mock_result.data.return_value = []  # Empty result
        
        result = db.execute_query("MATCH (n) RETURN n")
        
        assert result == []

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_large_result_handling(self, mock_session, mock_driver):
        """Test handling of large query results."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        
        # Large result set
        large_result = [{"id": i, "data": f"item_{i}"} for i in range(1000)]
        mock_result.data.return_value = large_result
        
        result = db.execute_query("MATCH (n) RETURN n")
        
        assert len(result) == 1000
        assert result[0]["id"] == 0
        assert result[999]["id"] == 999

    @patch('src.database.GraphDatabase.driver')
    @patch('src.database.GraphDatabase.session')
    def test_complex_query_parameters(self, mock_session, mock_driver):
        """Test query execution with complex parameters."""
        mock_driver.return_value = MagicMock()
        mock_driver.return_value.verify_connectivity.return_value = True
        
        mock_session.return_value.__enter__.return_value = MagicMock()
        
        mock_result = MagicMock()
        mock_session.return_value.__enter__.return_value.run.return_value = mock_result
        mock_result.data.return_value = [{"result": "complex"}]
        
        complex_params = {
            "names": ["Alice", "Bob", "Charlie"],
            "age_range": {"min": 25, "max": 50},
            "active": True
        }
        
        result = db.execute_query(
            "MATCH (n) WHERE n.name IN $names AND n.age >= $age_range.min AND n.active = $active RETURN n",
            complex_params
        )
        
        assert result == [{"result": "complex"}]
        mock_session.return_value.__enter__.return_value.run.assert_called_once_with(
            "MATCH (n) WHERE n.name IN $names AND n.age >= $age_range.min AND n.active = $active RETURN n",
            complex_params
        )


if __name__ == "__main__":
    pytest.main([__file__])

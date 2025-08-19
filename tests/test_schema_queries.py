#!/usr/bin/env python3
"""
Script to query the actual database schema and understand the correct relationships.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.database import db

def query_schema():
    """Query the actual database schema."""
    
    print("🔍 Querying Actual Database Schema")
    print("=" * 60)
    
    try:
        
        # Query 1: Get all node labels
        print("1. Node Labels:")
        result = db.execute_query("CALL db.labels() YIELD label RETURN label ORDER BY label")
        for row in result:
            print(f"   - {row['label']}")
        
        print()
        
        # Query 2: Get all relationship types
        print("2. Relationship Types:")
        result = db.execute_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
        for row in result:
            print(f"   - {row['relationshipType']}")
        
        print()
        
        # Query 3: Get sample relationships for each type
        print("3. Sample Relationships:")
        result = db.execute_query("CALL db.relationshipTypes() YIELD relationshipType")
        for row in result:
            rel_type = row['relationshipType']
            print(f"   {rel_type}:")
            try:
                sample = db.execute_query(f"MATCH ()-[r:{rel_type}]->() RETURN type(r), startNode(r), endNode(r) LIMIT 3")
                for s in sample:
                    start_labels = list(s['startNode(r)'].labels)
                    end_labels = list(s['endNode(r)'].labels)
                    print(f"     ({start_labels}) -[:{rel_type}]-> ({end_labels})")
            except Exception as e:
                print(f"     Error querying {rel_type}: {e}")
            print()
        
        # Query 4: Get properties for each node type
        print("4. Node Properties:")
        result = db.execute_query("CALL db.labels() YIELD label")
        for row in result:
            label = row['label']
            print(f"   {label}:")
            try:
                props = db.execute_query(f"MATCH (n:{label}) RETURN keys(n) as properties LIMIT 1")
                if props:
                    properties = props[0]['properties']
                    for prop in sorted(properties):
                        print(f"     - {prop}")
            except Exception as e:
                print(f"     Error querying properties: {e}")
            print()
        
        # Query 5: Test the specific query that was failing
        print("5. Testing DiffTest Class Query:")
        queries_to_test = [
            "MATCH (c:Class {name: 'DiffTest'})<-[:DEFINES]-(f:File)-[:DECLARES]->(m:Method) RETURN m.name, m.line LIMIT 5",
            "MATCH (c:Class {name: 'DiffTest'})-[:DEFINED_BY]->(f:File)<-[:DECLARED_BY]-(m:Method) RETURN m.name, m.line LIMIT 5",
            "MATCH (c:Class {name: 'DiffTest'})-[:DEFINED_BY]->(f:File)-[:DECLARES]->(m:Method) RETURN m.name, m.line LIMIT 5",
            "MATCH (c:Class {name: 'DiffTest'})-[:DEFINED_BY]->(f:File)<-[:DECLARED_BY]-(m:Method) RETURN m.name, m.line LIMIT 5",
        ]
        
        for i, query in enumerate(queries_to_test, 1):
            print(f"   Query {i}: {query}")
            try:
                result = db.execute_query(query)
                print(f"     Results: {len(result)} rows")
                if result:
                    for row in result[:3]:
                        print(f"       {row}")
            except Exception as e:
                print(f"     Error: {e}")
            print()
        
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")

def main():
    """Main function."""
    query_schema()

if __name__ == "__main__":
    main()

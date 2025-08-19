#!/usr/bin/env python3
"""
Test script to verify dynamic schema generation from database.
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.tools import tool_registry

def test_dynamic_schema():
    """Test the dynamic schema generation."""
    
    print("🔍 Testing Dynamic Schema Generation")
    print("=" * 60)
    
    try:
        # Get the dynamic schema context
        schema_context = tool_registry._get_database_schema_context()
        
        print("✅ Schema generated successfully")
        print(f"📏 Schema length: {len(schema_context)} characters")
        print()
        
        print("📋 Generated Schema:")
        print("-" * 40)
        print(schema_context)
        print("-" * 40)
        
        # Test if it contains expected sections
        expected_sections = [
            "NODE LABELS:",
            "RELATIONSHIP TYPES:", 
            "RELATIONSHIP PATTERNS:",
            "NODE PROPERTIES:",
            "COMMON QUERY PATTERNS:",
            "EXAMPLE QUERIES:"
        ]
        
        print("\n🔍 Schema Validation:")
        for section in expected_sections:
            if section in schema_context:
                print(f"✅ {section}")
            else:
                print(f"❌ {section} - Missing")
        
        # Test if it contains actual database data
        if "Class" in schema_context and "Method" in schema_context:
            print("✅ Contains actual node labels from database")
        else:
            print("❌ Missing actual node labels")
            
        if "CONTAINS_METHOD" in schema_context and "DEFINES" in schema_context:
            print("✅ Contains actual relationship types from database")
        else:
            print("❌ Missing actual relationship types")
            
    except Exception as e:
        print(f"❌ Error testing dynamic schema: {e}")
        import traceback
        traceback.print_exc()

async def test_text2cypher_with_dynamic_schema():
    """Test text2cypher with the dynamic schema."""
    
    print("\n🧪 Testing Text2Cypher with Dynamic Schema")
    print("=" * 60)
    
    try:
        # Test the text2cypher tool
        result = await tool_registry.async_execute_tool("text2cypher", {
            "question": "List all the Methods under DiffTest Class"
        })
        
        print(f"✅ Text2Cypher execution successful")
        print(f"📊 Result count: {result.get('result_count', 0)}")
        print(f"🔍 Generated query: {result.get('generated_query', 'N/A')}")
        print(f"📋 Results: {len(result.get('results', []))}")
        
        if result.get('results'):
            print(f"📋 Sample results:")
            for i, row in enumerate(result['results'][:3]):
                print(f"  {i+1}. {row}")
                
    except Exception as e:
        print(f"❌ Text2Cypher test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main function."""
    test_dynamic_schema()
    await test_text2cypher_with_dynamic_schema()
    
    print("\n🎯 Dynamic Schema Test Complete!")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

if __name__ == "__main__":
    main()

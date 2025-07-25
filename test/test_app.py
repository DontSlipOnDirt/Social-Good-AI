#!/usr/bin/env python3
"""
Test script for the Crime Query Assistant application.
This script tests various components without requiring the full Streamlit interface.
"""

import sys
import os
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils import config
from engines.llm_local import parse_query_with_ollama
from engines.llm_openai import parse_query_with_openai
from engines.query_builder import build_mongo_query, translate_synonyms
from data.ingest_to_mongo import ingest_sample_data, query_crime_data, get_database_stats
from utils.language_utils import detect_language, translate_text, extract_entities
from utils.logger import log_error, log_query

def test_language_utils():
    """Test language detection and translation utilities."""
    print("\n=== Testing Language Utils ===")
    
    test_queries = [
        "Show me all theft crimes in Berlin since February 15th",
        "मुझे दिल्ली में फरवरी से अब तक हुई चोरी दिखाओ।",
        "ఫిబ్రవరి నుండి హైదరాబాద్‌లో జరిగిన అన్ని దొంగతనాలు చూపించండి"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Test language detection
        detected_lang = detect_language(query)
        print(f"Detected language: {detected_lang}")
        
        # Test translation
        if detected_lang != 'en':
            translated = translate_text(query, 'en')
            print(f"Translated: {translated}")
        
        # Test entity extraction
        entities = extract_entities(query)
        print(f"Entities: {entities}")

def test_llm_parsing():
    """Test LLM query parsing."""
    print("\n=== Testing LLM Parsing ===")
    
    test_queries = [
        "Show me all theft crimes in Berlin since February 15th",
        "Find assault cases in New York from January to March 2024",
        "List all open burglary cases reported by police"
    ]
    
    for query in test_queries:
        print(f"\nTesting query: {query}")
        
        # Test with available LLM engine
        try:
            if config.LLM_ENGINE == "ollama":
                print("Testing with Ollama...")
                start_time = time.time()
                result = parse_query_with_ollama(query, config.LLM_MODEL_NAME)
                end_time = time.time()
                print(f"Ollama result: {result}")
                print(f"Processing time: {end_time - start_time:.2f}s")
            elif config.LLM_ENGINE == "openai":
                print("Testing with OpenAI...")
                start_time = time.time()
                result = parse_query_with_openai(query, config.LLM_MODEL_NAME)
                end_time = time.time()
                print(f"OpenAI result: {result}")
                print(f"Processing time: {end_time - start_time:.2f}s")
        except Exception as e:
            print(f"Error testing LLM: {str(e)}")
            # Create a mock result for testing
            result = {
                "crime_type": "theft",
                "location": "Berlin",
                "date_start": "2024-02-15",
                "date_end": None,
                "status": None,
                "reported_by": None
            }
        
        # Test query building
        if "error" not in result:
            result = translate_synonyms(result)
            mongo_query = build_mongo_query(result)
            print(f"MongoDB query: {mongo_query}")

def test_mongodb_operations():
    """Test MongoDB operations."""
    print("\n=== Testing MongoDB Operations ===")
    
    try:
        # Test sample data ingestion
        print("Ingesting sample data...")
        if ingest_sample_data():
            print("✓ Sample data ingested successfully")
        else:
            print("✗ Failed to ingest sample data")
            return
        
        # Test database stats
        print("\nGetting database stats...")
        stats = get_database_stats()
        print(f"Database stats: {stats}")
        
        # Test queries
        test_queries = [
            {"crime_type": {"$regex": "theft", "$options": "i"}},
            {"city": {"$regex": "Berlin", "$options": "i"}},
            {"status": "open"},
            {"date": {"$gte": datetime(2024, 2, 1)}}
        ]
        
        for query in test_queries:
            print(f"\nTesting query: {query}")
            start_time = time.time()
            results = query_crime_data(query)
            end_time = time.time()
            print(f"Results: {len(results)} records found")
            print(f"Query time: {end_time - start_time:.2f}s")
            
            if results:
                print("Sample result:")
                print(results[0])
    
    except Exception as e:
        print(f"Error testing MongoDB: {str(e)}")

def test_end_to_end():
    """Test end-to-end functionality."""
    print("\n=== Testing End-to-End Functionality ===")
    
    test_queries = [
        "Show me all theft crimes in Berlin",
        "Find open cases in Delhi",
        "List burglary incidents from February 2024"
    ]
    
    for query in test_queries:
        print(f"\n--- Processing: {query} ---")
        
        try:
            # Step 1: Language detection
            detected_lang = detect_language(query)
            print(f"1. Detected language: {detected_lang}")
            
            # Step 2: Translation (if needed)
            processed_query = query
            if detected_lang != 'en':
                processed_query = translate_text(query, 'en')
                print(f"2. Translated query: {processed_query}")
            else:
                print("2. No translation needed")
            
            # Step 3: LLM parsing (mock for testing)
            print("3. Parsing with LLM...")
            parsed_query = {
                "crime_type": "theft" if "theft" in processed_query.lower() else "burglary" if "burglary" in processed_query.lower() else None,
                "location": "Berlin" if "Berlin" in processed_query else "Delhi" if "Delhi" in processed_query else None,
                "date_start": "2024-02-01" if "February" in processed_query else None,
                "date_end": None,
                "status": "open" if "open" in processed_query.lower() else None,
                "reported_by": None
            }
            print(f"   Parsed query: {parsed_query}")
            
            # Step 4: Query building
            parsed_query = translate_synonyms(parsed_query)
            mongo_query = build_mongo_query(parsed_query)
            print(f"4. MongoDB query: {mongo_query}")
            
            # Step 5: Database query
            start_time = time.time()
            results = query_crime_data(mongo_query)
            end_time = time.time()
            print(f"5. Query results: {len(results)} records found in {end_time - start_time:.2f}s")
            
            # Log the operation
            log_query(query, len(results), end_time - start_time)
            
        except Exception as e:
            print(f"Error in end-to-end test: {str(e)}")
            log_error(f"End-to-end test error: {str(e)}")

def main():
    """Run all tests."""
    print("Crime Query Assistant - Test Suite")
    print("=" * 50)
    
    # Test individual components
    test_language_utils()
    test_llm_parsing()
    test_mongodb_operations()
    test_end_to_end()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")
    print("\nTo run the full application:")
    print("1. Make sure MongoDB is running")
    print("2. Install requirements: pip install -r requirements.txt")
    print("3. Run: streamlit run main.py")

if __name__ == "__main__":
    main()


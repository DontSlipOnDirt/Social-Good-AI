#!/usr/bin/env python3
"""
Simplified test script for the Crime Query Assistant application.
Tests basic functionality without requiring heavy dependencies.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test configuration loading."""
    print("=== Testing Configuration ===")
    try:
        from utils import config
        print(f"✓ STT Engine: {config.STT_ENGINE}")
        print(f"✓ LLM Engine: {config.LLM_ENGINE}")
        print(f"✓ LLM Model: {config.LLM_MODEL_NAME}")
        print(f"✓ Translation: {config.TRANSLATE_TO_ENGLISH}")
        print(f"✓ MongoDB URI: {config.MONGODB_URI}")
        return True
    except Exception as e:
        print(f"✗ Config test failed: {str(e)}")
        return False

def test_query_builder():
    """Test query builder without external dependencies."""
    print("\n=== Testing Query Builder ===")
    try:
        from engines.query_builder import build_mongo_query, translate_synonyms
        
        # Test query building
        test_parsed_query = {
            "crime_type": "theft",
            "location": "Berlin",
            "date_start": "2024-02-15",
            "date_end": None,
            "status": "open",
            "reported_by": None
        }
        
        # Test synonym translation
        translated = translate_synonyms(test_parsed_query.copy())
        print(f"✓ Synonym translation: {translated}")
        
        # Test MongoDB query building
        mongo_query = build_mongo_query(translated)
        print(f"✓ MongoDB query: {mongo_query}")
        
        # Test with Hindi crime type
        hindi_query = {"crime_type": "चोरी", "location": "Delhi"}
        translated_hindi = translate_synonyms(hindi_query)
        print(f"✓ Hindi synonym translation: {translated_hindi}")
        
        return True
    except Exception as e:
        print(f"✗ Query builder test failed: {str(e)}")
        return False

def test_logger():
    """Test logging functionality."""
    print("\n=== Testing Logger ===")
    try:
        from utils.logger import log_info, log_error, log_query
        
        log_info("Test info message")
        log_error("Test error message")
        log_query("test query", 5, 1.23)
        
        print("✓ Logger functions work correctly")
        return True
    except Exception as e:
        print(f"✗ Logger test failed: {str(e)}")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("\n=== Testing File Structure ===")
    
    required_files = [
        "main.py",
        "config.py",
        "requirements.txt",
        "README.md",
        "engines/stt_whisper.py",
        "engines/stt_google.py",
        "engines/llm_local.py",
        "engines/llm_openai.py",
        "engines/query_builder.py",
        "data/ingest_to_mongo.py",
        "utils/language_utils.py",
        "utils/logger.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    else:
        print("✓ All required files present")
        return True

def test_sample_data_structure():
    """Test sample data structure."""
    print("\n=== Testing Sample Data Structure ===")
    try:
        from data.ingest_to_mongo import create_sample_data
        
        sample_data = create_sample_data()
        print(f"✓ Created {len(sample_data)} sample records")
        
        # Verify data structure
        required_fields = ["crime_type", "location", "city", "date", "status"]
        for i, record in enumerate(sample_data[:2]):  # Check first 2 records
            for field in required_fields:
                if field not in record:
                    print(f"✗ Missing field '{field}' in record {i}")
                    return False
            print(f"✓ Record {i}: {record['crime_type']} in {record['city']}")
        
        return True
    except Exception as e:
        print(f"✗ Sample data test failed: {str(e)}")
        return False

def main():
    """Run simplified tests."""
    print("Crime Query Assistant - Simplified Test Suite")
    print("=" * 50)
    
    tests = [
        test_config,
        test_file_structure,
        test_query_builder,
        test_logger,
        test_sample_data_structure
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! The application structure is correct.")
    else:
        print("✗ Some tests failed. Check the output above for details.")
    
    print("\nNext steps:")
    print("1. Install dependencies: pip install streamlit pymongo")
    print("2. Start MongoDB: mongod")
    print("3. Run the app: streamlit run main.py")

if __name__ == "__main__":
    main()


#!/usr/bin/env python3
"""
Core test suite for enhanced crime query application features.
Tests dynamic data handling, pagination, and search functionality without UI dependencies.
"""

import unittest
import json
import math
from datetime import datetime
from unittest.mock import Mock, patch

# Import modules to test (avoiding Streamlit dependencies)
from engines.data_handler import DynamicDataHandler, process_variable_json

class TestDynamicDataHandler(unittest.TestCase):
    """Test cases for dynamic data handling functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = DynamicDataHandler()
        
        # Sample sparse query
        self.sparse_query = {
            "crime_type": None,
            "location": "Maharashtra",
            "date_start": None,
            "date_end": None,
            "status": None,
            "reported_by": None
        }
        
        # Sample record array
        self.record_array = [
            {
                "id": 1,
                "date": "2023-02-10",
                "location": "Borivali, Mumbai, Maharashtra",
                "crime_category": "Burglary",
                "status": "Under Investigation"
            },
            {
                "id": 2,
                "date": "2023-02-22",
                "location": "Thane, Mumbai, Maharashtra",
                "crime_category": "Theft",
                "status": "Under Investigation"
            }
        ]
    
    def test_detect_data_format_query_object(self):
        """Test detection of query object format."""
        format_type = self.handler.detect_data_format(self.sparse_query)
        self.assertEqual(format_type, "query_object")
        print("✓ Query object format detection works")
    
    def test_detect_data_format_record_array(self):
        """Test detection of record array format."""
        format_type = self.handler.detect_data_format(self.record_array)
        self.assertEqual(format_type, "record_array")
        print("✓ Record array format detection works")
    
    def test_normalize_query_object(self):
        """Test normalization of query objects."""
        normalized = self.handler.normalize_query_object(self.sparse_query)
        
        # Should only contain non-null fields
        self.assertIn("location", normalized)
        self.assertEqual(normalized["location"], "Maharashtra")
        self.assertNotIn("crime_type", normalized)
        self.assertNotIn("date_start", normalized)
        print("✓ Query object normalization works")
    
    def test_build_search_filters(self):
        """Test building search filters from normalized query."""
        normalized = self.handler.normalize_query_object(self.sparse_query)
        filters = self.handler.build_search_filters(normalized)
        
        # Should contain location filters
        self.assertIn("$or", filters)
        self.assertTrue(any("location" in condition for condition in filters["$or"]))
        print("✓ Search filter building works")
    
    def test_search_record_array(self):
        """Test searching within record arrays."""
        results = self.handler.search_record_array(self.record_array, "Maharashtra")
        
        # Should return both records as they both contain "Maharashtra"
        self.assertEqual(len(results), 2)
        print("✓ Record array search works")
    
    def test_search_record_array_specific_term(self):
        """Test searching for specific terms."""
        results = self.handler.search_record_array(self.record_array, "Burglary")
        
        # Should return only the burglary record
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["crime_category"], "Burglary")
        print("✓ Specific term search works")
    
    def test_partial_match_text_fields(self):
        """Test partial matching on text fields."""
        results = self.handler.partial_match_text_fields(
            self.record_array, "location", "Mumbai"
        )
        
        # Should return both records as they both contain "Mumbai"
        self.assertEqual(len(results), 2)
        print("✓ Partial text matching works")
    
    def test_handle_null_empty_fields(self):
        """Test handling of null and empty fields."""
        test_data = [
            {"field1": "value1", "field2": None, "field3": ""},
            {"field1": "value2", "field2": "value", "field3": []}
        ]
        
        cleaned = self.handler.handle_null_empty_fields(test_data)
        
        # Null and empty fields should be replaced with "N/A"
        self.assertEqual(cleaned[0]["field2"], "N/A")
        self.assertEqual(cleaned[0]["field3"], "N/A")
        self.assertEqual(cleaned[1]["field3"], "N/A")
        print("✓ Null/empty field handling works")
    
    def test_process_dynamic_data_query_object(self):
        """Test processing query objects."""
        results = self.handler.process_dynamic_data(self.sparse_query)
        
        # Should return metadata about the query
        self.assertEqual(len(results), 1)
        self.assertIn("query_filters", results[0])
        self.assertEqual(results[0]["format"], "query_object")
        print("✓ Dynamic query object processing works")
    
    def test_process_dynamic_data_record_array(self):
        """Test processing record arrays."""
        results = self.handler.process_dynamic_data(self.record_array, "Maharashtra")
        
        # Should return filtered records
        self.assertEqual(len(results), 2)
        # Should have cleaned null fields
        for record in results:
            self.assertNotIn(None, record.values())
        print("✓ Dynamic record array processing works")

class TestProcessVariableJson(unittest.TestCase):
    """Test cases for variable JSON processing."""
    
    def test_process_json_string(self):
        """Test processing JSON strings."""
        json_string = json.dumps([{"id": 1, "location": "Mumbai"}])
        results = process_variable_json(json_string, "Mumbai")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["location"], "Mumbai")
        print("✓ JSON string processing works")
    
    def test_process_invalid_json_string(self):
        """Test handling of invalid JSON strings."""
        invalid_json = "{'invalid': json}"
        results = process_variable_json(invalid_json)
        
        # Should return empty list for invalid JSON
        self.assertEqual(len(results), 0)
        print("✓ Invalid JSON handling works")
    
    def test_process_dict_directly(self):
        """Test processing dictionaries directly."""
        test_dict = {"crime_type": "theft", "location": "Delhi"}
        results = process_variable_json(test_dict)
        
        # Should process as query object
        self.assertEqual(len(results), 1)
        self.assertIn("query_filters", results[0])
        print("✓ Direct dictionary processing works")

class TestPaginationLogic(unittest.TestCase):
    """Test cases for pagination logic."""
    
    def test_pagination_calculation(self):
        """Test pagination calculations."""
        total_results = 25
        results_per_page = 10
        
        total_pages = math.ceil(total_results / results_per_page)
        self.assertEqual(total_pages, 3)
        
        # Test page bounds
        page_number = 2
        start_idx = (page_number - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        
        self.assertEqual(start_idx, 10)
        self.assertEqual(end_idx, 20)
        print("✓ Pagination calculation works")
    
    def test_pagination_last_page(self):
        """Test pagination on last page."""
        total_results = 25
        results_per_page = 10
        page_number = 3
        
        start_idx = (page_number - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        
        self.assertEqual(start_idx, 20)
        self.assertEqual(end_idx, 25)  # Should not exceed total results
        print("✓ Last page pagination works")

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_end_to_end_query_processing(self):
        """Test complete query processing pipeline."""
        handler = DynamicDataHandler()
        
        # Simulate a complete query
        query = {
            "crime_type": "theft",
            "location": "Mumbai",
            "date_start": None,
            "date_end": None,
            "status": "open",
            "reported_by": None
        }
        
        # Process the query
        normalized = handler.normalize_query_object(query)
        filters = handler.build_search_filters(normalized)
        
        # Should have proper filters
        self.assertIn("$or", filters)
        self.assertIn("status", filters)
        print("✓ End-to-end query processing works")
    
    def test_multilingual_data_handling(self):
        """Test handling of multilingual data."""
        multilingual_records = [
            {"crime_type": "theft", "description": "Bicycle stolen"},
            {"crime_type": "चोरी", "description": "मोबाइल फोन चोरी"},
            {"crime_type": "దొంగతనం", "description": "లాప్‌టాప్ దొంగతనం"}
        ]
        
        handler = DynamicDataHandler()
        results = handler.search_record_array(multilingual_records, "theft")
        
        # Should find the English record
        self.assertTrue(len(results) >= 1)
        
        # Test Hindi search
        results_hindi = handler.search_record_array(multilingual_records, "चोरी")
        self.assertTrue(len(results_hindi) >= 1)
        print("✓ Multilingual data handling works")

def run_core_tests():
    """Run core test suites."""
    print("Running core test suite for enhanced features...")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDynamicDataHandler))
    test_suite.addTest(unittest.makeSuite(TestProcessVariableJson))
    test_suite.addTest(unittest.makeSuite(TestPaginationLogic))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=1, stream=open('/dev/null', 'w'))
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_core_tests()
    exit(0 if success else 1)


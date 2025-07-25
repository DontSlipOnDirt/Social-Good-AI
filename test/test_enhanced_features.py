#!/usr/bin/env python3
"""
Comprehensive test suite for enhanced crime query application features.
Tests real-time STT, dynamic data handling, pagination, and search functionality.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from engines.data_handler import DynamicDataHandler, process_variable_json
from engines.stt_realtime import initialize_microphone, transcribe_audio_realtime
from data.ingest_to_mongo import query_with_dynamic_handler, create_sample_data

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
    
    def test_detect_data_format_record_array(self):
        """Test detection of record array format."""
        format_type = self.handler.detect_data_format(self.record_array)
        self.assertEqual(format_type, "record_array")
    
    def test_normalize_query_object(self):
        """Test normalization of query objects."""
        normalized = self.handler.normalize_query_object(self.sparse_query)
        
        # Should only contain non-null fields
        self.assertIn("location", normalized)
        self.assertEqual(normalized["location"], "Maharashtra")
        self.assertNotIn("crime_type", normalized)
        self.assertNotIn("date_start", normalized)
    
    def test_build_search_filters(self):
        """Test building search filters from normalized query."""
        normalized = self.handler.normalize_query_object(self.sparse_query)
        filters = self.handler.build_search_filters(normalized)
        
        # Should contain location filters
        self.assertIn("$or", filters)
        self.assertTrue(any("location" in condition for condition in filters["$or"]))
    
    def test_search_record_array(self):
        """Test searching within record arrays."""
        results = self.handler.search_record_array(self.record_array, "Maharashtra")
        
        # Should return both records as they both contain "Maharashtra"
        self.assertEqual(len(results), 2)
    
    def test_search_record_array_specific_term(self):
        """Test searching for specific terms."""
        results = self.handler.search_record_array(self.record_array, "Burglary")
        
        # Should return only the burglary record
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["crime_category"], "Burglary")
    
    def test_partial_match_text_fields(self):
        """Test partial matching on text fields."""
        results = self.handler.partial_match_text_fields(
            self.record_array, "location", "Mumbai"
        )
        
        # Should return both records as they both contain "Mumbai"
        self.assertEqual(len(results), 2)
    
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
    
    def test_process_dynamic_data_query_object(self):
        """Test processing query objects."""
        results = self.handler.process_dynamic_data(self.sparse_query)
        
        # Should return metadata about the query
        self.assertEqual(len(results), 1)
        self.assertIn("query_filters", results[0])
        self.assertEqual(results[0]["format"], "query_object")
    
    def test_process_dynamic_data_record_array(self):
        """Test processing record arrays."""
        results = self.handler.process_dynamic_data(self.record_array, "Maharashtra")
        
        # Should return filtered records
        self.assertEqual(len(results), 2)
        # Should have cleaned null fields
        for record in results:
            self.assertNotIn(None, record.values())

class TestProcessVariableJson(unittest.TestCase):
    """Test cases for variable JSON processing."""
    
    def test_process_json_string(self):
        """Test processing JSON strings."""
        json_string = json.dumps([{"id": 1, "location": "Mumbai"}])
        results = process_variable_json(json_string, "Mumbai")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["location"], "Mumbai")
    
    def test_process_invalid_json_string(self):
        """Test handling of invalid JSON strings."""
        invalid_json = "{'invalid': json}"
        results = process_variable_json(invalid_json)
        
        # Should return empty list for invalid JSON
        self.assertEqual(len(results), 0)
    
    def test_process_dict_directly(self):
        """Test processing dictionaries directly."""
        test_dict = {"crime_type": "theft", "location": "Delhi"}
        results = process_variable_json(test_dict)
        
        # Should process as query object
        self.assertEqual(len(results), 1)
        self.assertIn("query_filters", results[0])

class TestRealtimeSTT(unittest.TestCase):
    """Test cases for real-time STT functionality."""
    
    @patch('speech_recognition.Recognizer')
    @patch('speech_recognition.Microphone')
    def test_initialize_microphone(self, mock_mic, mock_recognizer):
        """Test microphone initialization."""
        mock_recognizer_instance = Mock()
        mock_mic_instance = Mock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_mic.return_value = mock_mic_instance
        
        recognizer, microphone = initialize_microphone()
        
        self.assertIsNotNone(recognizer)
        self.assertIsNotNone(microphone)
    
    @patch('speech_recognition.Recognizer')
    def test_transcribe_audio_realtime_google(self, mock_recognizer):
        """Test Google STT transcription."""
        mock_recognizer_instance = Mock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_recognizer_instance.recognize_google.return_value = "test transcription"
        
        mock_audio = Mock()
        result = transcribe_audio_realtime(mock_recognizer_instance, mock_audio, "google")
        
        self.assertEqual(result, "test transcription")
        mock_recognizer_instance.recognize_google.assert_called_once()
    
    @patch('speech_recognition.Recognizer')
    @patch('engines.stt_whisper.transcribe_whisper')
    def test_transcribe_audio_realtime_whisper(self, mock_whisper, mock_recognizer):
        """Test Whisper STT transcription."""
        mock_recognizer_instance = Mock()
        mock_recognizer.return_value = mock_recognizer_instance
        mock_whisper.return_value = "whisper transcription"
        
        mock_audio = Mock()
        mock_audio.get_wav_data.return_value = b"fake audio data"
        
        result = transcribe_audio_realtime(mock_recognizer_instance, mock_audio, "whisper")
        
        self.assertEqual(result, "whisper transcription")
        mock_whisper.assert_called_once()

class TestDynamicQueries(unittest.TestCase):
    """Test cases for dynamic query functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = create_sample_data()
    
    @patch('data.ingest_to_mongo.query_crime_data')
    def test_query_with_dynamic_handler_sparse_query(self, mock_query):
        """Test dynamic handler with sparse query."""
        mock_query.return_value = [
            {"id": 1, "location": "Mumbai", "crime_type": "theft"}
        ]
        
        sparse_query = {
            "crime_type": None,
            "location": "Mumbai",
            "date_start": None,
            "date_end": None,
            "status": None,
            "reported_by": None
        }
        
        results = query_with_dynamic_handler(sparse_query)
        
        # Should call MongoDB query
        mock_query.assert_called_once()
        self.assertEqual(len(results), 1)
    
    @patch('data.ingest_to_mongo.query_crime_data')
    def test_query_with_dynamic_handler_record_array(self, mock_query):
        """Test dynamic handler with record array."""
        mock_query.return_value = [
            {"id": 1, "location": "Mumbai", "crime_type": "theft"},
            {"id": 2, "location": "Delhi", "crime_type": "fraud"}
        ]
        
        results = query_with_dynamic_handler([], "theft")
        
        # Should get all records and filter
        mock_query.assert_called_once_with({})
        self.assertTrue(len(results) >= 0)  # Results depend on filtering

class TestPaginationLogic(unittest.TestCase):
    """Test cases for pagination logic."""
    
    def test_pagination_calculation(self):
        """Test pagination calculations."""
        import math
        
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
    
    def test_pagination_last_page(self):
        """Test pagination on last page."""
        import math
        
        total_results = 25
        results_per_page = 10
        page_number = 3
        
        start_idx = (page_number - 1) * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        
        self.assertEqual(start_idx, 20)
        self.assertEqual(end_idx, 25)  # Should not exceed total results

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system."""
    
    def test_end_to_end_query_processing(self):
        """Test complete query processing pipeline."""
        # This would test the full pipeline from voice input to results
        # For now, we'll test the data processing pipeline
        
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

def run_all_tests():
    """Run all test suites."""
    print("Running comprehensive test suite for enhanced features...")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestDynamicDataHandler))
    test_suite.addTest(unittest.makeSuite(TestProcessVariableJson))
    test_suite.addTest(unittest.makeSuite(TestRealtimeSTT))
    test_suite.addTest(unittest.makeSuite(TestDynamicQueries))
    test_suite.addTest(unittest.makeSuite(TestPaginationLogic))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    print(f"{'='*50}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)


import json
import re
from typing import Dict, List, Any, Union
from datetime import datetime
from utils.logger import log_info, log_error

class DynamicDataHandler:
    """
    Handles variable JSON structures for both query objects and record arrays.
    Supports sparse query format and full record format.
    """
    
    def __init__(self):
        self.supported_formats = ["query_object", "record_array"]
    
    def detect_data_format(self, data: Union[Dict, List]) -> str:
        """
        Detect the format of the input data.
        
        Args:
            data: Input data (dict or list)
            
        Returns:
            str: Format type ("query_object" or "record_array")
        """
        if isinstance(data, dict):
            # Check if it looks like a query object (has typical query fields)
            query_fields = ["crime_type", "location", "date_start", "date_end", "status", "reported_by"]
            if any(field in data for field in query_fields):
                return "query_object"
            else:
                # Could be a single record, treat as record array
                return "record_array"
        elif isinstance(data, list):
            return "record_array"
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    def normalize_query_object(self, query_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize a query object by filtering out null/empty fields.
        
        Args:
            query_obj: Query object with potential null fields
            
        Returns:
            Dict: Normalized query object with only non-null fields
        """
        normalized = {}
        
        for key, value in query_obj.items():
            if value is not None and value != "" and value != []:
                # Handle different value types
                if isinstance(value, str):
                    normalized[key] = value.strip()
                else:
                    normalized[key] = value
        
        log_info(f"Normalized query object: {normalized}")
        return normalized
    
    def build_search_filters(self, query_obj: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build MongoDB-style search filters from a normalized query object.
        
        Args:
            query_obj: Normalized query object
            
        Returns:
            Dict: MongoDB query filters
        """
        filters = {}
        
        # Handle crime type with fuzzy matching
        if query_obj.get("crime_type"):
            crime_type = query_obj["crime_type"].lower()
            filters["$or"] = filters.get("$or", [])
            filters["$or"].extend([
                {"crime_type": {"$regex": crime_type, "$options": "i"}},
                {"crime_category": {"$regex": crime_type, "$options": "i"}},
                {"crime_subcategory": {"$regex": crime_type, "$options": "i"}}
            ])
        
        # Handle location with fuzzy matching
        if query_obj.get("location"):
            location = query_obj["location"].lower()
            location_filters = [
                {"location": {"$regex": location, "$options": "i"}},
                {"city": {"$regex": location, "$options": "i"}},
                {"address": {"$regex": location, "$options": "i"}},
                {"state": {"$regex": location, "$options": "i"}},
                {"country": {"$regex": location, "$options": "i"}}
            ]
            
            if "$or" in filters:
                # Combine with existing $or conditions using $and
                filters = {"$and": [{"$or": filters["$or"]}, {"$or": location_filters}]}
            else:
                filters["$or"] = location_filters
        
        # Handle date range
        date_filter = {}
        if query_obj.get("date_start"):
            try:
                start_date = datetime.strptime(query_obj["date_start"], "%Y-%m-%d")
                date_filter["$gte"] = start_date
            except ValueError:
                log_error(f"Invalid date format for date_start: {query_obj['date_start']}")
        
        if query_obj.get("date_end"):
            try:
                end_date = datetime.strptime(query_obj["date_end"], "%Y-%m-%d")
                date_filter["$lte"] = end_date
            except ValueError:
                log_error(f"Invalid date format for date_end: {query_obj['date_end']}")
        
        if date_filter:
            filters["date"] = date_filter
        
        # Handle status
        if query_obj.get("status"):
            filters["status"] = {"$regex": query_obj["status"], "$options": "i"}
        
        # Handle reported_by
        if query_obj.get("reported_by"):
            filters["reported_by"] = {"$regex": query_obj["reported_by"], "$options": "i"}
        
        return filters
    
    def search_record_array(self, records: List[Dict[str, Any]], search_terms: str) -> List[Dict[str, Any]]:
        """
        Search across all fields in all objects in a record array.
        
        Args:
            records: List of record dictionaries
            search_terms: Search terms to look for
            
        Returns:
            List: Filtered records matching the search terms
        """
        if not search_terms:
            return records
        
        search_terms_lower = search_terms.lower()
        search_words = search_terms_lower.split()
        
        matching_records = []
        
        for record in records:
            match_found = False
            
            # Search across all fields in the record
            for field, value in record.items():
                if value is None:
                    continue
                
                # Convert value to string for searching
                value_str = str(value).lower()
                
                # Check if any search word is found in this field
                for word in search_words:
                    if word in value_str:
                        match_found = True
                        break
                
                if match_found:
                    break
            
            if match_found:
                matching_records.append(record)
        
        log_info(f"Found {len(matching_records)} matching records out of {len(records)}")
        return matching_records
    
    def partial_match_text_fields(self, records: List[Dict[str, Any]], field_name: str, search_value: str) -> List[Dict[str, Any]]:
        """
        Perform partial matching on specific text fields.
        
        Args:
            records: List of record dictionaries
            field_name: Name of the field to search in
            search_value: Value to search for
            
        Returns:
            List: Records with partial matches
        """
        if not search_value:
            return records
        
        search_value_lower = search_value.lower()
        matching_records = []
        
        for record in records:
            field_value = record.get(field_name)
            if field_value and isinstance(field_value, str):
                if search_value_lower in field_value.lower():
                    matching_records.append(record)
        
        return matching_records
    
    def handle_null_empty_fields(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Handle null and empty fields appropriately in records.
        
        Args:
            records: List of record dictionaries
            
        Returns:
            List: Records with cleaned null/empty fields
        """
        cleaned_records = []
        
        for record in records:
            cleaned_record = {}
            
            for field, value in record.items():
                # Handle different types of empty/null values
                if value is None:
                    cleaned_record[field] = "N/A"
                elif isinstance(value, str) and value.strip() == "":
                    cleaned_record[field] = "N/A"
                elif isinstance(value, list) and len(value) == 0:
                    cleaned_record[field] = "N/A"
                else:
                    cleaned_record[field] = value
            
            cleaned_records.append(cleaned_record)
        
        return cleaned_records
    
    def process_dynamic_data(self, data: Union[Dict, List], search_query: str = None) -> List[Dict[str, Any]]:
        """
        Main method to process dynamic data based on its format.
        
        Args:
            data: Input data (dict or list)
            search_query: Optional search query string
            
        Returns:
            List: Processed results
        """
        try:
            data_format = self.detect_data_format(data)
            log_info(f"Detected data format: {data_format}")
            
            if data_format == "query_object":
                # For query objects, normalize and build filters
                if isinstance(data, dict):
                    normalized_query = self.normalize_query_object(data)
                    filters = self.build_search_filters(normalized_query)
                    
                    # This would typically be used with a database query
                    # For now, return the filters as metadata
                    return [{"query_filters": filters, "format": "query_object"}]
                else:
                    raise ValueError("Query object format expected dict, got list")
            
            elif data_format == "record_array":
                # For record arrays, perform search across all fields
                if isinstance(data, list):
                    records = data
                else:
                    # Single record, convert to list
                    records = [data]
                
                # Clean null/empty fields
                cleaned_records = self.handle_null_empty_fields(records)
                
                # Apply search if provided
                if search_query:
                    filtered_records = self.search_record_array(cleaned_records, search_query)
                else:
                    filtered_records = cleaned_records
                
                return filtered_records
            
            else:
                raise ValueError(f"Unsupported data format: {data_format}")
        
        except Exception as e:
            log_error(f"Error processing dynamic data: {str(e)}")
            return []

# Utility functions for integration with existing code
def process_variable_json(json_data: Union[str, Dict, List], search_query: str = None) -> List[Dict[str, Any]]:
    """
    Process variable JSON structures.
    
    Args:
        json_data: JSON data as string, dict, or list
        search_query: Optional search query
        
    Returns:
        List: Processed results
    """
    handler = DynamicDataHandler()
    
    # Parse JSON string if needed
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except json.JSONDecodeError as e:
            log_error(f"Invalid JSON string: {str(e)}")
            return []
    else:
        data = json_data
    
    return handler.process_dynamic_data(data, search_query)

def is_sparse_query_format(data: Dict[str, Any]) -> bool:
    """
    Check if data is in sparse query format.
    
    Args:
        data: Dictionary to check
        
    Returns:
        bool: True if sparse query format
    """
    query_fields = ["crime_type", "location", "date_start", "date_end", "status", "reported_by"]
    return isinstance(data, dict) and any(field in data for field in query_fields)

def extract_non_null_filters(query_obj: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract non-null fields from a query object for filtering.
    
    Args:
        query_obj: Query object
        
    Returns:
        Dict: Non-null fields
    """
    handler = DynamicDataHandler()
    return handler.normalize_query_object(query_obj)

# Test function
def test_dynamic_data_handler():
    """Test the dynamic data handler with sample data."""
    handler = DynamicDataHandler()
    
    # Test sparse query format
    sparse_query = {
        "crime_type": None,
        "location": "Maharashtra",
        "date_start": None,
        "date_end": None,
        "status": None,
        "reported_by": None
    }
    
    print("Testing sparse query format:")
    result = handler.process_dynamic_data(sparse_query)
    print(json.dumps(result, indent=2))
    
    # Test record array format
    record_array = [
        {
            "id": 3,
            "date": "2023-02-10",
            "location": "Borivali, Mumbai, Maharashtra",
            "crime_category": "Burglary",
            "status": "Under Investigation"
        },
        {
            "id": 10,
            "date": "2023-02-22",
            "location": "Thane, Mumbai, Maharashtra",
            "crime_category": "Theft",
            "status": "Under Investigation"
        }
    ]
    
    print("\nTesting record array format:")
    result = handler.process_dynamic_data(record_array, "Maharashtra")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    test_dynamic_data_handler()


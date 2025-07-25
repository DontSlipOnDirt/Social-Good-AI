import pandas as pd
import pymongo
import json
import os
import sys
from datetime import datetime

# Adjust sys.path if needed for your project structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import config
from utils.logger import log_info, log_error
from engines.data_handler import DynamicDataHandler

def connect_to_mongodb():
    """Connect to MongoDB database."""
    try:
        client = pymongo.MongoClient(config.MONGODB_URI)
        db = client[config.MONGODB_DB_NAME]
        collection = db[config.MONGODB_COLLECTION_NAME]
        log_info(f"Connected to MongoDB: {config.MONGODB_URI} -> DB: {config.MONGODB_DB_NAME} | Collection: {config.MONGODB_COLLECTION_NAME}")
        return client, db, collection
    except Exception as e:
        log_error(f"Error connecting to MongoDB: {str(e)}")
        return None, None, None

def create_sample_data():
    """Create sample multilingual crime data."""
    sample_data = [
        {
            "crime_category": "theft",
            "location": "Berlin",
            "city": "Berlin",
            "address": "Alexanderplatz 1",
            "date": datetime(2024, 2, 15),
            "status": "open",
            "reported_by": "citizen",
            "description": "Bicycle stolen from parking area"
        },
        {
            "crime_category": "चोरी",  # Hindi for theft
            "location": "Delhi",
            "city": "Delhi",
            "address": "Connaught Place",
            "date": datetime(2024, 2, 20),
            "status": "closed",
            "reported_by": "police",
            "description": "मोबाइल फोन चोरी"  # Mobile phone theft in Hindi
        },
        {
            "crime_category": "దొంగతనం",  # Telugu for theft
            "location": "Hyderabad",
            "city": "Hyderabad",
            "address": "HITEC City",
            "date": datetime(2024, 3, 1),
            "status": "open",
            "reported_by": "citizen",
            "description": "లాప్‌టాప్ దొంగతనం"  # Laptop theft in Telugu
        },
        {
            "crime_category": "assault",
            "location": "New York",
            "city": "New York",
            "address": "Times Square",
            "date": datetime(2024, 1, 10),
            "status": "solved",
            "reported_by": "witness",
            "description": "Physical altercation between two individuals"
        },
        {
            "crime_category": "burglary",
            "location": "London",
            "city": "London",
            "address": "Baker Street 221B",
            "date": datetime(2024, 2, 28),
            "status": "open",
            "reported_by": "victim",
            "description": "House break-in, valuables stolen"
        },
        {
            "crime_category": "fraud",
            "location": "Mumbai",
            "city": "Mumbai",
            "address": "Bandra West",
            "date": datetime(2024, 3, 5),
            "status": "open",
            "reported_by": "bank",
            "description": "Credit card fraud case"
        },
        # Additional Maharashtra records for better testing
        {
            "crime_category": "theft",
            "location": "Pune",
            "city": "Pune",
            "state": "Maharashtra",
            "address": "FC Road",
            "date": datetime(2024, 2, 12),
            "status": "under investigation",
            "reported_by": "citizen",
            "description": "Mobile phone theft from restaurant"
        },
        {
            "crime_category": "burglary",
            "location": "Nashik",
            "city": "Nashik",
            "state": "Maharashtra",
            "address": "College Road",
            "date": datetime(2024, 1, 25),
            "status": "open",
            "reported_by": "resident",
            "description": "House burglary during night hours"
        }
    ]
    return sample_data

def ingest_csv_to_mongo(csv_file_path: str):
    """Ingest CSV data into MongoDB."""
    try:
        client, db, collection = connect_to_mongodb()
        if collection is None:
            return False

        df = pd.read_csv(csv_file_path)
        records = df.to_dict('records')

        # Convert date strings to datetime objects if needed
        for record in records:
            if 'date' in record and isinstance(record['date'], str):
                try:
                    record['date'] = datetime.strptime(record['date'], '%Y-%m-%d')
                except ValueError:
                    try:
                        record['date'] = datetime.strptime(record['date'], '%d/%m/%Y')
                    except ValueError:
                        record['date'] = datetime.now()

        result = collection.insert_many(records)
        log_info(f"Inserted {len(result.inserted_ids)} records into MongoDB")
        client.close()
        return True

    except Exception as e:
        log_error(f"Error ingesting CSV to MongoDB: {str(e)}")
        return False

def ingest_json_to_mongo(json_file_path: str):
    """Ingest JSON data into MongoDB."""
    try:
        client, db, collection = connect_to_mongodb()
        if collection is None:
            return False

        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Convert date_reported fields if present
        for record in data:
            if 'date_reported' in record and isinstance(record['date_reported'], str):
                try:
                    record['date_reported'] = datetime.strptime(record['date_reported'], '%Y-%m-%d')
                except ValueError:
                    record['date_reported'] = datetime.now()

        collection.delete_many({})  # Clear old data
        result = collection.insert_many(data)
        log_info(f"Inserted {len(result.inserted_ids)} JSON records into MongoDB")
        client.close()
        return True

    except Exception as e:
        log_error(f"Error ingesting JSON to MongoDB: {str(e)}")
        return False

def ingest_sample_data():
    """Ingest sample data into MongoDB."""
    try:
        client, db, collection = connect_to_mongodb()
        if collection is None:
            return False

        collection.delete_many({})
        sample_data = create_sample_data()
        result = collection.insert_many(sample_data)
        log_info(f"Inserted {len(result.inserted_ids)} sample records into MongoDB")
        client.close()
        return True

    except Exception as e:
        log_error(f"Error ingesting sample data: {str(e)}")
        return False

def query_crime_data(mongo_query: dict):
    """Query crime data from MongoDB with enhanced dynamic data handling."""
    try:
        client, db, collection = connect_to_mongodb()
        if collection is None:
            return []

        cursor = collection.find(mongo_query)
        results = list(cursor)

        # Convert ObjectId to string & datetime to string for JSON serialization
        for result in results:
            if '_id' in result:
                result['_id'] = str(result['_id'])
            if 'date' in result and isinstance(result['date'], datetime):
                result['date'] = result['date'].strftime('%Y-%m-%d')
            if 'date_reported' in result and isinstance(result['date_reported'], datetime):
                result['date_reported'] = result['date_reported'].strftime('%Y-%m-%d')

        client.close()
        log_info(f"Query returned {len(results)} results")
        return results

    except Exception as e:
        log_error(f"Error querying MongoDB: {str(e)}")
        return []

def query_with_dynamic_handler(query_data, search_terms=None):
    """
    Query crime data using the dynamic data handler.

    Args:
        query_data: Query data (dict or list)
        search_terms: Optional search terms for text search

    Returns:
        List: Query results
    """
    try:
        handler = DynamicDataHandler()
        data_format = handler.detect_data_format(query_data)

        if data_format == "query_object":
            normalized_query = handler.normalize_query_object(query_data)
            from engines.query_builder import build_mongo_query
            mongo_query = build_mongo_query(normalized_query)
            return query_crime_data(mongo_query)

        elif data_format == "record_array":
            all_records = query_crime_data({})
            if search_terms:
                filtered_records = handler.search_record_array(all_records, search_terms)
            else:
                filtered_records = all_records
            return handler.handle_null_empty_fields(filtered_records)

        else:
            log_error(f"Unsupported data format: {data_format}")
            return []

    except Exception as e:
        log_error(f"Error in dynamic query: {str(e)}")
        return []

def get_database_stats():
    """Get database statistics."""
    try:
        client, db, collection = connect_to_mongodb()
        if collection is None:
            return {}

        stats = {
            "total_records": collection.count_documents({}),
            "crime_categorys": list(collection.distinct("crime_category")),
            "cities": list(collection.distinct("city")),
            "statuses": list(collection.distinct("status"))
        }
        client.close()
        return stats

    except Exception as e:
        log_error(f"Error getting database stats: {str(e)}")
        return {}

def test_dynamic_queries():
    """Test dynamic query functionality."""
    print("Testing dynamic query functionality...")

    sparse_query = {
        "crime_category": None,
        "location": "Maharashtra",
        "date_start": None,
        "date_end": None,
        "status": None,
        "reported_by": None
    }

    print("\n1. Testing sparse query format:")
    results = query_with_dynamic_handler(sparse_query)
    print(f"Found {len(results)} results for Maharashtra")

    print("\n2. Testing record array search:")
    results = query_with_dynamic_handler([], "theft")
    print(f"Found {len(results)} results for 'theft'")

    full_query = {
        "crime_category": "theft",
        "location": "Mumbai",
        "status": "open"
    }

    print("\n3. Testing full query:")
    results = query_with_dynamic_handler(full_query)
    print(f"Found {len(results)} results for theft in Mumbai with open status")

if __name__ == "__main__":
    print("Testing MongoDB connection and ingestion...")

    json_path = os.path.join(os.path.dirname(__file__), 'tt_crime_dataset_merged.json')

    if ingest_json_to_mongo(json_path):
        print("Sample data ingested successfully!")

        test_query = {"crime_category": {"$regex": "theft", "$options": "i"}}
        results = query_crime_data(test_query)
        print(f"Test query returned {len(results)} results")

        stats = get_database_stats()
        print("Database stats:", stats)

        test_dynamic_queries()
    else:
        print("Failed to ingest sample data. Check MongoDB connection.")

# To run
# cd to demo_git
# python data/ingest_to_mongo.py C:\Users\ninad\PycharmProjects\Demo_Crime_Query\demo_git\data\tt_crime_dataset_merged.json
# crime_data_db - crimes

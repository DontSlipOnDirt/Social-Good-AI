import json
import sqlite3
import pandas as pd
from typing import Any, Dict, List, Union
import os

def flatten_json(data: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """
    Flatten a nested JSON object.
    
    Args:
        data: JSON data to flatten
        parent_key: Parent key for nested items
        sep: Separator for nested keys
    
    Returns:
        Flattened dictionary
    """
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Handle lists by converting to string or creating separate entries
            if v and isinstance(v[0], dict):
                # If list contains dictionaries, flatten each one
                for i, item in enumerate(v):
                    if isinstance(item, dict):
                        items.extend(flatten_json(item, f"{new_key}_{i}", sep=sep).items())
                    else:
                        items.append((f"{new_key}_{i}", item))
            else:
                # Simple list - convert to comma-separated string
                items.append((new_key, ', '.join(map(str, v)) if v else None))
        else:
            items.append((new_key, v))
    return dict(items)

def infer_sql_type(value: Any) -> str:
    """
    Infer SQL data type from Python value.
    
    Args:
        value: Python value to analyze
    
    Returns:
        SQL data type string
    """
    if value is None:
        return "TEXT"
    elif isinstance(value, bool):
        return "BOOLEAN"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "REAL"
    else:
        return "TEXT"

def create_table_schema(data: List[Dict[str, Any]], table_name: str) -> str:
    """
    Create SQL table schema from data.
    
    Args:
        data: List of dictionaries representing rows
        table_name: Name of the table
    
    Returns:
        SQL CREATE TABLE statement
    """
    if not data:
        return f"CREATE TABLE {table_name} (id INTEGER PRIMARY KEY);"
    
    # Get all possible columns from all records
    all_columns = set()
    for record in data:
        all_columns.update(record.keys())
    
    # Infer types for each column by sampling values
    column_types = {}
    for col in all_columns:
        sample_values = [record.get(col) for record in data if record.get(col) is not None]
        if sample_values:
            # Use the first non-null value to infer type
            column_types[col] = infer_sql_type(sample_values[0])
        else:
            column_types[col] = "TEXT"
    
    # Create schema
    columns = []
    has_id_column = 'id' in all_columns
    
    for col, sql_type in column_types.items():
        # Clean column name (replace spaces and special chars with underscores)
        clean_col = col.replace(' ', '_').replace('-', '_').replace('.', '_')
        
        # If this is the existing 'id' column, make it PRIMARY KEY
        if col == 'id' and has_id_column:
            columns.append(f"{clean_col} {sql_type} PRIMARY KEY")
        else:
            columns.append(f"{clean_col} {sql_type}")
    
    # Create the schema string without backslashes in f-string
    columns_str = ',\n    '.join(columns)
    
    # Only add auto-increment id if there's no existing id column
    if has_id_column:
        return f"CREATE TABLE {table_name} (\n    {columns_str}\n);"
    else:
        return f"CREATE TABLE {table_name} (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    {columns_str}\n);"

def json_to_sql_database(json_file_path: str, db_file_path: str, table_name: str = "data", flatten: bool = True):
    """
    Convert JSON file to SQLite database.
    
    Args:
        json_file_path: Path to input JSON file
        db_file_path: Path to output SQLite database file
        table_name: Name of the table to create
        flatten: Whether to flatten nested JSON objects
    """
    
    # Read JSON file
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: JSON file '{json_file_path}' not found.")
        return
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return
    
    # Handle different JSON structures
    if isinstance(json_data, dict):
        # Single object - convert to list
        if flatten:
            json_data = [flatten_json(json_data)]
        else:
            json_data = [json_data]
    elif isinstance(json_data, list):
        # List of objects
        if flatten and json_data and isinstance(json_data[0], dict):
            json_data = [flatten_json(item) if isinstance(item, dict) else item for item in json_data]
    else:
        print("Error: JSON must be an object or array of objects.")
        return
    
    # Create database connection
    try:
        conn = sqlite3.connect(db_file_path)
        cursor = conn.cursor()
        
        # Drop table if exists
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Create table schema
        schema = create_table_schema(json_data, table_name)
        print(f"Creating table with schema:\n{schema}")
        cursor.execute(schema)
        
        # Insert data
        if json_data:
            # Get all columns from schema
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            # Check if we have an existing id column or auto-increment
            has_existing_id = any(col[1] == 'id' and 'AUTOINCREMENT' not in col[2].upper() for col in columns_info)
            
            if has_existing_id:
                # Use all columns including the existing id
                columns = [col[1] for col in columns_info]
            else:
                # Exclude auto-increment id column
                columns = [col[1] for col in columns_info if col[1] != 'id']
            
            # Prepare data for insertion
            insert_data = []
            for record in json_data:
                if isinstance(record, dict):
                    # Clean column names in record keys
                    clean_record = {}
                    for k, v in record.items():
                        clean_key = k.replace(' ', '_').replace('-', '_').replace('.', '_')
                        clean_record[clean_key] = v
                    
                    row = []
                    for col in columns:
                        value = clean_record.get(col)
                        # Handle None values and convert complex types to strings
                        if value is None:
                            row.append(None)
                        elif isinstance(value, (dict, list)):
                            row.append(json.dumps(value))
                        else:
                            row.append(value)
                    insert_data.append(tuple(row))
                else:
                    # Handle non-dict items
                    insert_data.append((record,))
            
            # Insert data
            placeholders = ','.join(['?' for _ in columns])
            insert_query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
            cursor.executemany(insert_query, insert_data)
            
            print(f"Inserted {len(insert_data)} records into table '{table_name}'")
        
        # Commit and close
        conn.commit()
        conn.close()
        
        print(f"Database created successfully: {db_file_path}")
        
        # Display sample data
        conn = sqlite3.connect(db_file_path)
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print("\nSample data:")
        print(df.to_string())
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    """
    Convert the TT crime dataset to SQL database.
    """
    # Your specific file configuration
    json_file = "tt_crime_dataset_merged.json"
    db_file = "crime_database.db"
    table_name = "crime_records"
    
    # Check if JSON file exists
    if not os.path.exists(json_file):
        print(f"Error: JSON file '{json_file}' not found in current directory.")
        print("Please make sure the file 'tt_crime_dataset_merged.json' is in the same folder as this script.")
        return
    
    print(f"Processing crime dataset: {json_file}")
    print(f"Creating database: {db_file}")
    print(f"Table name: {table_name}")
    print("-" * 50)
    
    # Convert JSON to SQL database (no flattening needed for this structure)
    json_to_sql_database(json_file, db_file, table_name, flatten=False)
    
    # Additional analysis
    try:
        conn = sqlite3.connect(db_file)
        
        # Get total record count
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total_records = cursor.fetchone()[0]
        
        print(f"\n=== Database Statistics ===")
        print(f"Total records: {total_records}")
        
        # Crime category distribution
        print(f"\n=== Crime Categories ===")
        df_categories = pd.read_sql_query(f"""
            SELECT crime_category, COUNT(*) as count 
            FROM {table_name} 
            GROUP BY crime_category 
            ORDER BY count DESC
        """, conn)
        print(df_categories.to_string(index=False))
        
        # Status distribution
        print(f"\n=== Case Status Distribution ===")
        df_status = pd.read_sql_query(f"""
            SELECT status, COUNT(*) as count 
            FROM {table_name} 
            GROUP BY status 
            ORDER BY count DESC
        """, conn)
        print(df_status.to_string(index=False))
        
        conn.close()
        
    except Exception as e:
        print(f"Error generating statistics: {e}")

if __name__ == "__main__":
    main()
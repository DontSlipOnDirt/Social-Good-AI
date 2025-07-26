import streamlit as st
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import sqlite3
import pandas as pd
import time
import os
import re

# Page configuration
st.set_page_config(
    page_title="NL2SQL Crime Database Chat",
    page_icon="🔍",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "model_loaded" not in st.session_state:
    st.session_state.model_loaded = False

if "model" not in st.session_state:
    st.session_state.model = None

if "tokenizer" not in st.session_state:
    st.session_state.tokenizer = None

if "db_connected" not in st.session_state:
    st.session_state.db_connected = False

# Database connection function
@st.cache_resource
def connect_to_database(db_path):
    """Connect to the SQLite database and return connection info"""
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        
        # Get table info
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        # Get schema info for crime_records table
        cursor.execute("PRAGMA table_info(crime_records);")
        schema_info = cursor.fetchall()
        
        return conn, tables, schema_info
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None, None, None

# SQL execution function
def execute_sql_query(query, conn):
    """Execute SQL query and return results as DataFrame"""
    try:
        # Basic SQL injection prevention
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE', 'TRUNCATE']
        query_upper = query.upper()
        
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return None, f"Error: {keyword} operations are not allowed for security reasons."
        
        df = pd.read_sql_query(query, conn)
        return df, None
    except Exception as e:
        return None, str(e)

# Extract SQL from LLM response
def extract_sql_from_response(response):
    """Extract SQL query from LLM response"""
    # Clean the response
    response = response.strip()
    
    # Look for SQL in code blocks first
    sql_match = re.search(r'```(?:sql)?\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
    if sql_match:
        sql = sql_match.group(1).strip()
        if sql and 'SELECT' in sql.upper():
            return clean_sql_query(sql)
    
    # Split by common separators that indicate end of SQL
    separators = [
        'Explanation:',
        'This query',
        'The query',
        'Note:',
        'Here\'s how',
        'Breakdown:',
        '\n\n',  # Double newline often separates SQL from explanation
    ]
    
    # Find the first separator and extract everything before it
    sql_part = response
    for sep in separators:
        if sep in response:
            sql_part = response.split(sep)[0].strip()
            break
    
    # Look for SELECT statements in the cleaned part
    sql_patterns = [
        r'(SELECT\s+.*?;)',  # SELECT with semicolon
        r'(SELECT\s+.*?(?=\n[A-Z][a-z]))',  # SELECT until next sentence starts
        r'(SELECT\s+.*)',  # Any SELECT statement
    ]
    
    for pattern in sql_patterns:
        sql_match = re.search(pattern, sql_part, re.DOTALL | re.IGNORECASE)
        if sql_match:
            sql = sql_match.group(1).strip()
            # Basic validation - must contain FROM and be reasonable length
            if 'FROM' in sql.upper() and len(sql) < 1000:  # Prevent huge responses
                return clean_sql_query(sql)
    
    # If we still haven't found it, try line-by-line extraction
    lines = response.split('\n')
    sql_lines = []
    collecting = False
    
    for line in lines:
        line = line.strip()
        
        # Start collecting when we see SELECT
        if not collecting and 'SELECT' in line.upper():
            collecting = True
            sql_lines.append(line)
        elif collecting:
            # Stop collecting if we hit explanation keywords
            if any(keyword in line for keyword in ['Explanation:', 'This query', 'The query', 'Note:', 'Here\'s how', 'Breakdown:']):
                break
            # Stop if line looks like explanation (starts with "The" followed by explanation)
            elif line.startswith('The ') and any(word in line for word in ['function', 'clause', 'operator', 'query']):
                break
            # Continue collecting if it's SQL-like
            elif line and (any(keyword in line.upper() for keyword in ['FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'LIMIT', 'JOIN']) or line.endswith(';')):
                sql_lines.append(line)
                # Stop after semicolon
                if line.endswith(';'):
                    break
            # Stop if empty line after we've collected some SQL
            elif not line and sql_lines:
                break
            # Stop if line doesn't look like SQL
            elif line and not any(c in line for c in ['SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'LIMIT', '(', ')', ',', '*']):
                break
    
    if sql_lines:
        sql = ' '.join(sql_lines)
        if 'FROM' in sql.upper():
            return clean_sql_query(sql)
    
    # Last resort - return first line that looks like complete SQL
    lines = response.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if 'SELECT' in line.upper() and 'FROM' in line.upper():
            return clean_sql_query(line)
    
    # If nothing found, return a default error query
    return "SELECT 'Error: Could not extract valid SQL query from model response' as error_message;"

def clean_sql_query(sql):
    """Clean and format SQL query"""
    # Remove extra whitespace
    sql = ' '.join(sql.split())
    
    # Ensure it ends with semicolon
    if not sql.endswith(';'):
        sql += ';'
    
    # Fix common formatting issues
    sql = sql.replace(' ,', ',')  # Remove space before comma
    sql = sql.replace('( ', '(')   # Remove space after opening paren
    sql = sql.replace(' )', ')')   # Remove space before closing paren
    
    return sql

# Sidebar for configuration
with st.sidebar:
    st.header("🔍 NL2SQL Configuration")
    
    # Database section
    st.subheader("📊 Database")
    db_path = "data/crime_database.db"  # Hardcoded path
    st.info(f"Database: `{db_path}`")
    
    if st.button("🔌 Connect to Database"):
        if os.path.exists(db_path):
            conn, tables, schema_info = connect_to_database(db_path)
            if conn:
                st.session_state.db_conn = conn
                st.session_state.db_tables = tables
                st.session_state.db_schema = schema_info
                st.session_state.db_connected = True
                st.success("✅ Database connected successfully!")
            else:
                st.session_state.db_connected = False
        else:
            st.error(f"Database file '{db_path}' not found!")
            st.session_state.db_connected = False
    
    # Database status and schema
    if st.session_state.db_connected:
        st.success("✅ Database Connected")
        
        st.subheader("📋 Database Schema")
        st.write("**Table:** crime_records")
        
        # Display schema
        if hasattr(st.session_state, 'db_schema'):
            schema_df = pd.DataFrame(st.session_state.db_schema, 
                                   columns=['Column ID', 'Name', 'Type', 'NotNull', 'DefaultValue', 'PrimaryKey'])
            st.dataframe(schema_df[['Name', 'Type']], use_container_width=True)
        
        # Quick stats
        try:
            cursor = st.session_state.db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM crime_records")
            total_records = cursor.fetchone()[0]
            st.metric("Total Records", total_records)
        except:
            pass
    else:
        st.warning("⚠️ No database connected")
    
    st.divider()
    
    # Model selection
    st.subheader("🤖 Model Configuration")
    
    model_options = [
        "microsoft/CodeT5-base",
        "Salesforce/codet5p-770m",
        "meta-llama/Llama-2-7b-chat-hf",
        "codellama/CodeLlama-7b-Instruct-hf",
        "mistralai/Mistral-7B-Instruct-v0.1",
        "WizardLM/WizardCoder-3B-V1.0",
        "bigcode/starcoder2-7b",
        "microsoft/DialoGPT-large",
        "EleutherAI/gpt-neo-2.7B"
    ]
    
    model_choice = st.radio(
        "Model Selection:",
        ["Preset Models", "Custom Model"],
        index=0
    )
    
    if model_choice == "Preset Models":
        selected_model = st.selectbox(
            "Choose Model:",
            model_options,
            index=0
        )
    else:
        selected_model = st.text_input(
            "Enter Model Name:",
            placeholder="e.g., CodeLlama-7b-Instruct-hf",
            help="Enter any Hugging Face model name"
        )
    
    # Generation parameters
    temperature = st.slider("Temperature", 0.1, 1.0, 0.3, 0.1)
    max_tokens = st.slider("Max Tokens", 50, 500, 150, 25)
    
    # Load model button
    if st.button("🚀 Load Model", type="primary"):
        if model_choice == "Custom Model" and not selected_model:
            st.error("Please enter a model name first!")
        else:
            with st.spinner(f"Loading {selected_model}..."):
                try:
                    # Clear previous model from memory
                    if st.session_state.model is not None:
                        del st.session_state.model
                        del st.session_state.tokenizer
                        torch.cuda.empty_cache() if torch.cuda.is_available() else None
                    
                    # Load tokenizer and model
                    st.session_state.tokenizer = AutoTokenizer.from_pretrained(selected_model)
                    st.session_state.model = AutoModelForCausalLM.from_pretrained(
                        selected_model,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        device_map="auto" if torch.cuda.is_available() else None
                    )
                    
                    # Add padding token if it doesn't exist
                    if st.session_state.tokenizer.pad_token is None:
                        st.session_state.tokenizer.pad_token = st.session_state.tokenizer.eos_token
                    
                    st.session_state.model_loaded = True
                    st.session_state.current_model = selected_model
                    st.success(f"✅ {selected_model} loaded successfully!")
                    
                except Exception as e:
                    st.error(f"❌ Error loading model: {str(e)}")
                    st.session_state.model_loaded = False
    
    # Model status
    if st.session_state.model_loaded:
        st.success("✅ Model Ready")
        st.info(f"Using: {st.session_state.current_model}")
    else:
        st.warning("⚠️ No model loaded")
    
    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Main interface
st.title("🔍 NL2SQL Crime Database Chat")
st.markdown("Ask questions about the crime database in natural language!")

# Example queries
with st.expander("💡 Example Questions"):
    st.markdown("""
    - How many crimes were reported in total?
    - Show me all burglary cases
    - What are the different crime categories?
    - How many cases are still under investigation?
    - Show crimes reported in Mumbai
    - What's the distribution of crime statuses?
    - Show me crimes from February 2025
    """)

# Display chat messages
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                # Display SQL query
                if "sql_query" in message:
                    st.code(message["sql_query"], language="sql")
                
                # Display results or error
                if "dataframe" in message and message["dataframe"] is not None:
                    st.subheader("Query Results:")
                    st.dataframe(message["dataframe"], use_container_width=True)
                    st.info(f"Returned {len(message['dataframe'])} rows")
                elif "error" in message:
                    st.error(f"Query Error: {message['error']}")
                else:
                    st.markdown(message["content"])
            else:
                st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about the crime database..."):
    if not st.session_state.model_loaded:
        st.error("Please load a model first using the sidebar!")
        st.stop()
    
    if not st.session_state.db_connected:
        st.error("Please connect to the database first using the sidebar!")
        st.stop()
    
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        sql_placeholder = st.empty()
        result_placeholder = st.empty()
        
        with st.spinner("Generating SQL query..."):
            try:
                # Create NL2SQL prompt
                nl2sql_prompt = f"""You are a SQL expert. Convert the following natural language question into a SQL query for a crime database.

Database Schema:
Table: crime_records
Columns:
- id (INTEGER PRIMARY KEY): Unique identifier
- date (TEXT): Date of crime (YYYY-MM-DD format)
- time (TEXT): Time of crime (HH:MM format)
- location (TEXT): Location where crime occurred
- crime_category (TEXT): Type of crime (e.g., "Vandalism", "Fraud", "Burglary", "Assault")
- crime_subcategory (TEXT): Specific subtype of crime
- description (TEXT): Detailed description of the crime
- reported_by (TEXT): Who reported the crime
- status (TEXT): Case status (e.g., "Open", "Case Filed", "Under Investigation")

Rules:
1. Only generate SELECT queries - no INSERT, UPDATE, DELETE, DROP commands
2. Use proper SQL syntax for SQLite
3. Return only the SQL query, nothing else
4. Use LIKE operator for partial text matches
5. For counting, use COUNT(*)
6. For date filtering, remember dates are in 'YYYY-MM-DD' format

Question: {prompt}

SQL Query:"""

                # Tokenize input
                inputs = st.session_state.tokenizer.encode(
                    nl2sql_prompt,
                    return_tensors="pt",
                    truncation=True,
                    max_length=1024
                )
                
                # Move to GPU if available
                if torch.cuda.is_available():
                    inputs = inputs.to(st.session_state.model.device)
                
                # Generate response
                with torch.no_grad():
                    outputs = st.session_state.model.generate(
                        inputs,
                        max_new_tokens=max_tokens,
                        temperature=temperature,
                        do_sample=True,
                        pad_token_id=st.session_state.tokenizer.eos_token_id,
                        num_return_sequences=1,
                        early_stopping=True
                    )
                
                # Decode response
                response = st.session_state.tokenizer.decode(
                    outputs[0][len(inputs[0]):],
                    skip_special_tokens=True
                ).strip()
                
                # Extract SQL query
                sql_query = extract_sql_from_response(response)
                
                # Clean up the SQL query
                sql_query = sql_query.replace('\\n', '\n').strip()
                if not sql_query.endswith(';'):
                    sql_query += ';'
                
                # Display SQL query
                sql_placeholder.code(sql_query, language="sql")
                
                # Execute SQL query
                with st.spinner("Executing query..."):
                    df, error = execute_sql_query(sql_query, st.session_state.db_conn)
                    
                    if error:
                        result_placeholder.error(f"Query Error: {error}")
                        # Store error in message
                        message_data = {
                            "role": "assistant",
                            "content": "",
                            "sql_query": sql_query,
                            "error": error,
                            "dataframe": None
                        }
                    else:
                        # Display results
                        with result_placeholder.container():
                            st.subheader("Query Results:")
                            st.dataframe(df, use_container_width=True)
                            st.info(f"Returned {len(df)} rows")
                        
                        # Store successful result in message
                        message_data = {
                            "role": "assistant",
                            "content": "",
                            "sql_query": sql_query,
                            "dataframe": df,
                            "error": None
                        }
                
            except Exception as e:
                error_msg = f"Error generating query: {str(e)}"
                result_placeholder.error(error_msg)
                message_data = {
                    "role": "assistant",
                    "content": error_msg,
                    "sql_query": None,
                    "error": error_msg,
                    "dataframe": None
                }
    
    # Add assistant response to chat history
    st.session_state.messages.append(message_data)

# Footer with current status
if st.session_state.db_connected and st.session_state.model_loaded:
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Database:** `{db_path}` ✅")
    with col2:
        st.markdown(f"**Model:** `{st.session_state.current_model}` ✅")
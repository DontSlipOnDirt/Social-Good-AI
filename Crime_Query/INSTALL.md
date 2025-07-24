# Installation Guide

This guide will help you set up the Crime Query Assistant application on your system.

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: At least 4GB RAM (8GB recommended for Whisper models)
- **Storage**: At least 2GB free space (more for Whisper models)
- **Network**: Internet connection for Google STT and translation services

## Prerequisites

### 1. MongoDB Installation

#### Option A: Local MongoDB Installation

**Windows:**
1. Download MongoDB Community Server from https://www.mongodb.com/try/download/community
2. Run the installer and follow the setup wizard
3. Start MongoDB service: `net start MongoDB`

**macOS:**
```bash
# Using Homebrew
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community
```

**Linux (Ubuntu/Debian):**
```bash
# Import MongoDB public GPG key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Create list file for MongoDB
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update package database and install
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Option B: MongoDB Atlas (Cloud)

1. Create a free account at https://www.mongodb.com/atlas
2. Create a new cluster
3. Get your connection string
4. Update `config.py` with your Atlas connection string

### 2. Python Environment Setup

It's recommended to use a virtual environment:

```bash
# Create virtual environment
python -m venv crime_query_env

# Activate virtual environment
# On Windows:
crime_query_env\Scripts\activate
# On macOS/Linux:
source crime_query_env/bin/activate
```

## Installation Steps

### Step 1: Download the Application

```bash
# If you have the source code
cd crime-query-assistant

# Or clone from repository (if available)
git clone https://github.com/example/crime-query-assistant.git
cd crime-query-assistant
```

### Step 2: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

**Note**: If you encounter dependency conflicts, try installing packages individually:

```bash
# Core dependencies
pip install streamlit pandas pymongo

# Language processing
pip install langdetect googletrans==4.0.0rc1

# Optional: For local LLM support
pip install langchain langchain-community

# Optional: For Whisper STT
pip install openai-whisper torch
```

### Step 3: Configure the Application

1. Open `config.py` in a text editor
2. Modify settings as needed:

```python
# Speech-to-Text Engine
STT_ENGINE = "google"  # or "whisper"

# LLM Engine
LLM_ENGINE = "ollama"  # or "openai"
LLM_MODEL_NAME = "llama3"  # or your preferred model

# Translation
TRANSLATE_TO_ENGLISH = True

# MongoDB Connection
MONGODB_URI = "mongodb://localhost:27017/"  # or your Atlas connection string
MONGODB_DB_NAME = "crime_data_db"
MONGODB_COLLECTION_NAME = "crime_incidents"
```

### Step 4: Set Up Optional Components

#### For OpenAI API (if using OpenAI LLM):
```bash
# Set environment variable
export OPENAI_API_KEY="your-api-key-here"

# On Windows:
set OPENAI_API_KEY=your-api-key-here
```

#### For Ollama (if using local LLM):
1. Install Ollama from https://ollama.ai/
2. Pull a model:
```bash
ollama pull llama3
# or
ollama pull mistral
# or
model pull of your choice
```

### Step 5: Initialize Sample Data

```bash
# Run the data ingestion script
python data/ingest_to_mongo.py
```

### Step 6: Test the Installation

```bash
# Run the simplified test suite
python simple_test.py
```

### Step 7: Start the Application

```bash
# Launch the Streamlit app
streamlit run main.py
```

The application should open in your web browser at `http://localhost:8501`.

## Troubleshooting

### Common Issues

#### 1. MongoDB Connection Error
```
pymongo.errors.ServerSelectionTimeoutError: [Errno 111] Connection refused
```
**Solution**: Ensure MongoDB is running:
- Windows: `net start MongoDB`
- macOS: `brew services start mongodb/brew/mongodb-community`
- Linux: `sudo systemctl start mongod`

#### 2. Missing Dependencies
```
ModuleNotFoundError: No module named 'langchain'
```
**Solution**: Install missing packages:
```bash
pip install langchain langchain-community
```

#### 3. Whisper Model Download Issues
```
urllib.error.HTTPError: HTTP Error 403: Forbidden
```
**Solution**: 
- Check internet connection
- Try downloading manually: `python -c "import whisper; whisper.load_model('base')"`

#### 4. Google Translation API Errors
```
googletrans.exceptions.TranslationError
```
**Solution**: 
- Check internet connection
- Try using a different translation service or disable translation temporarily

#### 5. Streamlit Port Already in Use
```
OSError: [Errno 98] Address already in use
```
**Solution**: Use a different port:
```bash
streamlit run main.py --server.port 8502
```

### Performance Optimization

#### For Better Performance:
1. **Use SSD storage** for faster model loading
2. **Increase RAM** if using Whisper models
3. **Use GPU** for Whisper (install `torch` with CUDA support)
4. **Use local MongoDB** instead of Atlas for faster queries

#### Memory Usage:
- **Whisper base model**: ~1GB RAM
- **Whisper large model**: ~3GB RAM
- **Ollama models**: 2-8GB RAM depending on model size

## Verification

After installation, verify everything works:

1. **Configuration**: `python simple_test.py`
2. **Web Interface**: Open `http://localhost:8501`
3. **Database**: Check if sample data is loaded
4. **STT**: Try uploading an audio file
5. **LLM**: Test with a text query

## Getting Help

If you encounter issues:

1. Check the `logs/` directory for error messages
2. Run `python simple_test.py` to identify problems
3. Ensure all prerequisites are installed
4. Check the troubleshooting section above
5. Review the main README.md for additional information

## Next Steps

Once installed:
1. Review the main README.md for usage instructions
2. Try the example queries provided
3. Customize the configuration for your needs
4. Add your own crime data using the ingestion scripts

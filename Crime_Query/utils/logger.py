import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Configure logging
log_filename = os.path.join(
    log_dir,
    f"crime_query_app_{datetime.now().strftime('%d%m%Y_%H%M')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename),
        logging.StreamHandler()  # Also log to console
    ]
)

logger = logging.getLogger(__name__)

# Basic log functions
def log_info(message: str):
    """Log an info message."""
    logger.info(message)

def log_error(message: str):
    """Log an error message."""
    logger.error(message)

def log_warning(message: str):
    """Log a warning message."""
    logger.warning(message)

def log_debug(message: str):
    """Log a debug message."""
    logger.debug(message)

# Custom loggers
def log_query(query: str, results_count: int, processing_time: float):
    """Log query execution details."""
    log_info(f"Query: '{query}' | Results: {results_count} | Time: {processing_time:.2f}s")

def log_stt_operation(engine: str, audio_duration: float, transcription: str):
    """Log STT operation details."""
    log_info(f"STT Engine: {engine} | Audio Duration: {audio_duration:.2f}s | Transcription: '{transcription[:100]}...'")

def log_llm_operation(engine: str, model: str, query: str, response: str, response_time: float):
    """Log LLM operation details including full query and response."""
    log_info(f"LLM Engine: {engine} | Model: {model} | Time: {response_time:.2f}s")
    log_info(f"User Query: {query}")
    log_info(f"LLM Response: {response}")

def log_user_interaction(user_query: str, llm_response: str):
    """Log full user query and LLM response separately (alternative to above)."""
    logger.info(f"USER QUERY: {user_query}")
    logger.info(f"LLM RESPONSE: {llm_response}")

# Test when running directly
if __name__ == "__main__":
    log_info("Logger initialized successfully")
    log_error("This is a test error message")
    log_warning("This is a test warning message")
    log_debug("This is a test debug message")

    log_query("test query", 5, 1.23)
    log_stt_operation("whisper", 3.45, "This is a test transcription")
    log_llm_operation("ollama", "mistral", "test llm query", "test llm response", 2.67)
    log_user_interaction("Where is the highest crime?", "Delhi has the highest reported crime rate in 2023.")

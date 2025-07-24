from langdetect import detect, DetectorFactory
from googletrans import Translator
import re
from utils.logger import log_info, log_error

# Set seed for consistent language detection
DetectorFactory.seed = 0

def detect_language(text: str) -> str:
    """
    Detect the language of the input text.
    Returns ISO 639-1 language code (e.g., 'en', 'hi', 'te').
    """
    try:
        # Clean text for better detection
        cleaned_text = re.sub(r'[^\w\s]', '', text)
        if len(cleaned_text.strip()) < 3:
            return 'en'  # Default to English for very short text
        
        detected = detect(cleaned_text)
        log_info(f"Detected language: {detected}")
        return detected
    except Exception as e:
        log_error(f"Error detecting language: {str(e)}")
        return 'en'  # Default to English on error

def translate_text(text: str, target_lang: str = 'en', source_lang: str = 'auto') -> str:
    """
    Translate text from source language to target language.
    """
    try:
        translator = Translator()
        result = translator.translate(text, src=source_lang, dest=target_lang)
        translated_text = result.text
        log_info(f"Translated '{text}' to '{translated_text}'")
        return translated_text
    except Exception as e:
        log_error(f"Error translating text: {str(e)}")
        return text  # Return original text on error

def get_language_name(lang_code: str) -> str:
    """
    Get the full language name from ISO 639-1 code.
    """
    language_names = {
        'en': 'English',
        'hi': 'Hindi',
        'te': 'Telugu',
        'bho': 'Bhojpuri',
        'ms': 'Malay',
        'de': 'German',
        'fr': 'French',
        'es': 'Spanish',
        'it': 'Italian',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'zh': 'Chinese',
        'ar': 'Arabic',
        'ur': 'Urdu',
        'bn': 'Bengali',
        'ta': 'Tamil',
        'ml': 'Malayalam',
        'kn': 'Kannada',
        'gu': 'Gujarati',
        'pa': 'Punjabi',
        'mr': 'Marathi',
        'or': 'Odia',
        'as': 'Assamese'
    }
    return language_names.get(lang_code, lang_code.upper())

def get_stt_language_code(detected_lang: str) -> str:
    """
    Convert detected language code to STT-compatible language code.
    Different STT engines may use different language code formats.
    """
    # Google Speech Recognition language codes
    google_lang_codes = {
        'en': 'en-US',
        'hi': 'hi-IN',
        'te': 'te-IN',
        'de': 'de-DE',
        'fr': 'fr-FR',
        'es': 'es-ES',
        'it': 'it-IT',
        'pt': 'pt-PT',
        'ru': 'ru-RU',
        'ja': 'ja-JP',
        'ko': 'ko-KR',
        'zh': 'zh-CN',
        'ar': 'ar-SA',
        'ur': 'ur-PK',
        'bn': 'bn-BD',
        'ta': 'ta-IN',
        'ml': 'ml-IN',
        'kn': 'kn-IN',
        'gu': 'gu-IN',
        'pa': 'pa-IN',
        'mr': 'mr-IN'
    }
    return google_lang_codes.get(detected_lang, 'en-US')

def normalize_text(text: str) -> str:
    """
    Normalize text for better processing.
    """
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Convert to lowercase for processing (but preserve original case)
    return text

def extract_entities(text: str, lang: str = 'en') -> dict:
    """
    Extract common entities from text (dates, locations, etc.).
    This is a simple rule-based approach.
    """
    entities = {
        'dates': [],
        'locations': [],
        'numbers': []
    }
    
    # Extract dates (simple patterns)
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # DD/MM/YYYY or MM/DD/YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
        r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'
    ]
    
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities['dates'].extend(matches)
    
    # Extract numbers
    number_pattern = r'\b\d+\b'
    entities['numbers'] = re.findall(number_pattern, text)
    
    # Extract potential locations (capitalized words)
    location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    potential_locations = re.findall(location_pattern, text)
    
    # Filter out common words that aren't locations
    common_words = {'The', 'This', 'That', 'These', 'Those', 'And', 'Or', 'But', 'So', 'Yet', 'For', 'Nor'}
    entities['locations'] = [loc for loc in potential_locations if loc not in common_words]
    
    return entities

def get_supported_languages() -> list:
    """
    Get list of supported languages for the application.
    """
    return [
        {'code': 'en', 'name': 'English'},
        {'code': 'hi', 'name': 'Hindi'},
        {'code': 'te', 'name': 'Telugu'},
        {'code': 'bho', 'name': 'Bhojpuri'},
        {'code': 'ms', 'name': 'Malay'},
        {'code': 'de', 'name': 'German'},
        {'code': 'fr', 'name': 'French'},
        {'code': 'es', 'name': 'Spanish'},
        {'code': 'bn', 'name': 'Bengali'},
        {'code': 'ta', 'name': 'Tamil'},
        {'code': 'ur', 'name': 'Urdu'},
        {'code': 'ar', 'name': 'Arabic'}
    ]

if __name__ == "__main__":
    # Test the language utilities
    test_texts = [
        "Show me all theft crimes in Berlin since February 15th",
        "मुझे दिल्ली में फरवरी से अब तक हुई चोरी दिखाओ।",
        "ఫిబ్రవరి నుండి హైదరాబాద్‌లో జరిగిన అన్ని దొంగతనాలు చూపించండి"
    ]
    
    for text in test_texts:
        print(f"\nText: {text}")
        lang = detect_language(text)
        print(f"Detected language: {lang} ({get_language_name(lang)})")
        
        if lang != 'en':
            translated = translate_text(text, 'en')
            print(f"Translated: {translated}")
        
        entities = extract_entities(text, lang)
        print(f"Entities: {entities}")


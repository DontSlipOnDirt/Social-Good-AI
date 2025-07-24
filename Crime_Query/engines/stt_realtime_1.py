# has the input box different as chat_input

import streamlit as st
import speech_recognition as sr
import tempfile
import os
from utils.logger import log_info, log_error, log_stt_operation
from utils.language_utils import detect_language
import time

# Language mapping for speech recognition with extensive Indian language support
LANGUAGE_CODES = {
    # English
    'en': 'en-US',
    'en-in': 'en-IN',  # Indian English

    # Major Indian Languages (Official Languages)
    'hi': 'hi-IN',  # Hindi
    'bn': 'bn-IN',  # Bengali
    'te': 'te-IN',  # Telugu
    'ta': 'ta-IN',  # Tamil
    'mr': 'mr-IN',  # Marathi
    'gu': 'gu-IN',  # Gujarati
    'kn': 'kn-IN',  # Kannada
    'ml': 'ml-IN',  # Malayalam
    'or': 'or-IN',  # Odia
    'pa': 'pa-IN',  # Punjabi
    'as': 'as-IN',  # Assamese
    'ur': 'ur-IN',  # Urdu
    'sa': 'sa-IN',  # Sanskrit
    'ks': 'ks-IN',  # Kashmiri
    'sd': 'sd-IN',  # Sindhi
    'ne': 'ne-IN',  # Nepali
    'my': 'my-IN',  # Manipuri
    'kok': 'kok-IN',  # Konkani
    'mni': 'mni-IN',  # Meitei (Manipuri)
    'bodo': 'bodo-IN',  # Bodo
    'doi': 'doi-IN',  # Dogri
    'mai': 'mai-IN',  # Maithili
    'sat': 'sat-IN',  # Santali

    # Regional Indian Languages
    'bh': 'bh-IN',  # Bihari
    'raj': 'raj-IN',  # Rajasthani
    'bhb': 'bhb-IN',  # Bhili
    'gom': 'gom-IN',  # Goan Konkani
    'tcy': 'tcy-IN',  # Tulu
    'new': 'new-IN',  # Newari
    'bpy': 'bpy-IN',  # Bishnupriya
    'sck': 'sck-IN',  # Sadri

    # International Languages
    'es': 'es-ES',  # Spanish
    'fr': 'fr-FR',  # French
    'de': 'de-DE',  # German
    'it': 'it-IT',  # Italian
    'pt': 'pt-BR',  # Portuguese
    'ru': 'ru-RU',  # Russian
    'ja': 'ja-JP',  # Japanese
    'ko': 'ko-KR',  # Korean
    'zh': 'zh-CN',  # Chinese (Simplified)
    'zh-tw': 'zh-TW',  # Chinese (Traditional)
    'ar': 'ar-SA',  # Arabic
    'th': 'th-TH',  # Thai
    'vi': 'vi-VN',  # Vietnamese
    'id': 'id-ID',  # Indonesian
    'ms': 'ms-MY',  # Malay
    'fil': 'fil-PH',  # Filipino
    'sw': 'sw-KE',  # Swahili
    'tr': 'tr-TR',  # Turkish
    'fa': 'fa-IR',  # Persian
    'he': 'he-IL',  # Hebrew
    'pl': 'pl-PL',  # Polish
    'nl': 'nl-NL',  # Dutch
    'sv': 'sv-SE',  # Swedish
    'da': 'da-DK',  # Danish
    'no': 'no-NO',  # Norwegian
    'fi': 'fi-FI',  # Finnish
    'el': 'el-GR',  # Greek
    'cs': 'cs-CZ',  # Czech
    'sk': 'sk-SK',  # Slovak
    'hu': 'hu-HU',  # Hungarian
    'ro': 'ro-RO',  # Romanian
    'bg': 'bg-BG',  # Bulgarian
    'hr': 'hr-HR',  # Croatian
    'sr': 'sr-RS',  # Serbian
    'sl': 'sl-SI',  # Slovenian
    'et': 'et-EE',  # Estonian
    'lv': 'lv-LV',  # Latvian
    'lt': 'lt-LT',  # Lithuanian
    'mt': 'mt-MT',  # Maltese
    'is': 'is-IS',  # Icelandic
}


def initialize_microphone():
    """Initialize microphone for speech recognition."""
    try:
        r = sr.Recognizer()
        mic = sr.Microphone()

        # Adjust for ambient noise
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1)

        return r, mic
    except Exception as e:
        log_error(f"Error initializing microphone: {str(e)}")
        return None, None


def transcribe_voice_input(language_code="en-US", engine="google", timeout=10):
    """
    Record and transcribe voice input with language support.
    Returns (success, transcription, error_message)
    """
    try:
        # Initialize microphone
        recognizer, microphone = initialize_microphone()
        if not recognizer or not microphone:
            return False, "", "Could not initialize microphone"

        # Record audio
        log_info(f"Starting voice recording in {language_code}...")
        with microphone as source:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=8)

        log_info("Audio recorded, transcribing...")
        start_time = time.time()

        # Transcribe based on engine
        if engine == "google":
            transcription = recognizer.recognize_google(audio, language=language_code)
        elif engine == "whisper":
            # For Whisper, save audio to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                with open(tmp_file.name, 'wb') as f:
                    f.write(audio.get_wav_data())

                from engines.stt_whisper import transcribe_whisper
                transcription = transcribe_whisper(tmp_file.name)
                os.unlink(tmp_file.name)
        else:
            return False, "", f"Unsupported STT engine: {engine}"

        end_time = time.time()
        log_stt_operation(engine, end_time - start_time, transcription)

        return True, transcription.strip(), ""

    except sr.WaitTimeoutError:
        return False, "", "No speech detected - please try speaking louder or closer to the microphone"
    except sr.UnknownValueError:
        return False, "", "Could not understand the audio - please speak more clearly"
    except sr.RequestError as e:
        return False, "", f"Speech recognition service error: {str(e)}"
    except Exception as e:
        log_error(f"Voice input error: {str(e)}")
        return False, "", f"Voice input error: {str(e)}"


def create_integrated_input_component():
    """
    Create an integrated text and voice input component using st.chat_input.
    Returns the final query text when submitted.
    """

    # Initialize session states
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'voice_recording' not in st.session_state:
        st.session_state.voice_recording = False
    if 'pending_voice_text' not in st.session_state:
        st.session_state.pending_voice_text = ""
    if 'show_voice_confirmation' not in st.session_state:
        st.session_state.show_voice_confirmation = False

    # Language selection for voice input with comprehensive Indian language support
    col_lang, col_voice = st.columns([3, 1])

    with col_lang:
        # Create organized language options
        language_options = {
            # Indian English
            'en-in': '🇮🇳 Indian English',
            'en': '🇺🇸 English (US)',

            # Major Indian Languages (22 Official Languages)
            'hi': '🇮🇳 हिन्दी (Hindi)',
            'bn': '🇮🇳 বাংলা (Bengali)',
            'te': '🇮🇳 తెలుగు (Telugu)',
            'ta': '🇮🇳 தமிழ் (Tamil)',
            'mr': '🇮🇳 मराठी (Marathi)',
            'gu': '🇮🇳 ગુജરાતી (Gujarati)',
            'kn': '🇮🇳 ಕನ್ನಡ (Kannada)',
            'ml': '🇮🇳 മലയാളം (Malayalam)',
            'or': '🇮🇳 ଓଡ଼ିଆ (Odia)',
            'pa': '🇮🇳 ਪੰਜਾਬੀ (Punjabi)',
            'as': '🇮🇳 অসমীয়া (Assamese)',
            'ur': '🇮🇳 اردو (Urdu)',
            'sa': '🇮🇳 संस्कृत (Sanskrit)',
            'ks': '🇮🇳 कॉशुर (Kashmiri)',
            'sd': '🇮🇳 سنڌي (Sindhi)',
            'ne': '🇮🇳 नेपाली (Nepali)',
            'mni': '🇮🇳 মেইতেই (Manipuri)',
            'kok': '🇮🇳 कोंकणी (Konkani)',
            'bodo': '🇮🇳 बड़ो (Bodo)',
            'doi': '🇮🇳 डोगरी (Dogri)',
            'mai': '🇮🇳 मैथिली (Maithili)',
            'sat': '🇮🇳 ᱥᱟᱱᱛᱟᱲᱤ (Santali)',

            # Regional Indian Languages
            'bh': '🇮🇳 भोजपुरी (Bihari)',
            'raj': '🇮🇳 राजस्थानी (Rajasthani)',
            'bhb': '🇮🇳 भीली (Bhili)',
            'gom': '🇮🇳 गोंयची कोंकणी (Goan Konkani)',
            'tcy': '🇮🇳 ತುಳು (Tulu)',
            'new': '🇮🇳 नेवारी (Newari)',

            # International Languages
            'ar': '🇸🇦 العربية (Arabic)',
            'zh': '🇨🇳 中文 (Chinese)',
            'zh-tw': '🇹🇼 繁體中文 (Traditional Chinese)',
            'es': '🇪🇸 Español (Spanish)',
            'fr': '🇫🇷 Français (French)',
            'de': '🇩🇪 Deutsch (German)',
            'it': '🇮🇹 Italiano (Italian)',
            'pt': '🇧🇷 Português (Portuguese)',
            'ru': '🇷🇺 Русский (Russian)',
            'ja': '🇯🇵 日本語 (Japanese)',
            'ko': '🇰🇷 한국어 (Korean)',
            'th': '🇹🇭 ไทย (Thai)',
            'vi': '🇻🇳 Tiếng Việt (Vietnamese)',
            'id': '🇮🇩 Bahasa Indonesia',
            'ms': '🇲🇾 Bahasa Melayu (Malay)',
            'fil': '🇵🇭 Filipino',
            'tr': '🇹🇷 Türkçe (Turkish)',
            'fa': '🇮🇷 فارسی (Persian)',
            'he': '🇮🇱 עברית (Hebrew)',
            'sw': '🇰🇪 Kiswahili (Swahili)',
            'pl': '🇵🇱 Polski (Polish)',
            'nl': '🇳🇱 Nederlands (Dutch)',
            'sv': '🇸🇪 Svenska (Swedish)',
            'da': '🇩🇰 Dansk (Danish)',
            'no': '🇳🇴 Norsk (Norwegian)',
            'fi': '🇫🇮 Suomi (Finnish)',
            'el': '🇬🇷 Ελληνικά (Greek)',
            'cs': '🇨🇿 Čeština (Czech)',
            'sk': '🇸🇰 Slovenčina (Slovak)',
            'hu': '🇭🇺 Magyar (Hungarian)',
            'ro': '🇷🇴 Română (Romanian)',
        }

        selected_lang = st.selectbox(
            "🌍 Voice Language",
            options=list(language_options.keys()),
            format_func=lambda x: language_options.get(x, x.upper()),
            help="Select language for voice recognition. Indian languages are prioritized at the top.",
            index=0  # Default to Indian English
        )

    with col_voice:
        st.markdown("<br>", unsafe_allow_html=True)
        voice_button_disabled = st.session_state.voice_recording

        if st.button(
                "🎤" if not st.session_state.voice_recording else "⏹️",
                key="voice_input_btn",
                disabled=voice_button_disabled,
                help="Click to start/stop voice input"
        ):
            if not st.session_state.voice_recording:
                # Start recording
                st.session_state.voice_recording = True
                st.rerun()

    # Handle voice recording
    if st.session_state.voice_recording:
        with st.spinner(f"🎤 Listening in {selected_lang.upper()}... Speak now!"):
            # Get language code
            language_code = LANGUAGE_CODES.get(selected_lang, 'en-US')

            # Import config here to avoid circular imports
            from utils import config

            # Record and transcribe
            success, transcription, error_msg = transcribe_voice_input(
                language_code=language_code,
                engine=config.STT_ENGINE,
                timeout=10
            )

            # Reset recording state
            st.session_state.voice_recording = False

            if success and transcription:
                st.session_state.pending_voice_text = transcription
                st.session_state.show_voice_confirmation = True
                st.success(f"✅ Voice captured: '{transcription}'")
            else:
                st.error(f"❌ Voice input failed: {error_msg}")

            # Force rerun to update UI
            time.sleep(0.5)  # Brief pause for user to see the message
            st.rerun()

    # Voice confirmation dialog
    if st.session_state.show_voice_confirmation and st.session_state.pending_voice_text:
        st.info("🎤 **Voice Input Captured**")

        # Show transcribed text with edit option
        col_text, col_actions = st.columns([3, 1])

        with col_text:
            edited_voice_text = st.text_area(
                "Review and edit if needed:",
                value=st.session_state.pending_voice_text,
                height=80,
                key="voice_text_editor"
            )

        with col_actions:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ Use This", key="confirm_voice"):
                # Use the voice text and set it for the chat input
                st.session_state.current_query = edited_voice_text
                st.session_state.show_voice_confirmation = False
                st.session_state.pending_voice_text = ""

                # Set flag for auto-submit
                st.session_state.voice_submitted_query = edited_voice_text
                st.session_state.voice_auto_submit = True

                st.success("Voice input applied - Starting search...")
                st.rerun()

            if st.button("❌ Discard", key="discard_voice"):
                # Discard voice input
                st.session_state.show_voice_confirmation = False
                st.session_state.pending_voice_text = ""
                st.rerun()

    # Main chat input - this replaces the text_input and send button
    user_input = st.chat_input(
        "Enter your crime data query or use voice input above...",
        key="main_chat_input"
    )

    # Handle chat input submission
    if user_input:
        return user_input.strip()

    # Check for voice auto-submit
    if hasattr(st.session_state, 'voice_auto_submit') and st.session_state.voice_auto_submit:
        query_to_return = st.session_state.voice_submitted_query
        # Clean up the auto-submit flags
        del st.session_state.voice_auto_submit
        del st.session_state.voice_submitted_query
        return query_to_return

    return None


def create_example_queries_section():
    """Create example queries section with better integration."""
    st.markdown("**💡 Try these example queries:**")

    examples = [
        ("🏪 Burglaries in Mumbai", "Show me burglaries in Mumbai City"),
        ("💰 Thefts in Bihar", "Show me Thefts in Bihar"),
        ("🎭 Fraud in Chennai", "Show me Fraud in Chennai")
    ]

    cols = st.columns(3)
    for i, (label, query) in enumerate(examples):
        with cols[i % 3]:
            if st.button(label, key=f"example_{i}"):
                st.session_state.current_query = query
                st.rerun()


# Test function
def test_integrated_input():
    """Test the integrated input component."""
    st.title("🔍 Integrated Voice & Text Input Test")

    query = create_integrated_input_component()

    if query:
        st.success(f"Query submitted: {query}")

        # Detect language of the submitted query
        detected_lang = detect_language(query)
        st.info(f"Detected language: {detected_lang}")

    create_example_queries_section()


if __name__ == "__main__":
    test_integrated_input()
import streamlit as st
import pandas as pd
import json
import math

from utils import config
from engines.stt_realtime import create_integrated_input_component, create_example_queries_section
#from engines.stt_realtime_1 import create_integrated_input_component, create_example_queries_section
from engines.llm_local import parse_query_with_ollama
from engines.llm_openai import parse_query_with_openai
from engines.query_builder import build_mongo_query, translate_synonyms
from data.ingest_to_mongo import query_crime_data
from utils.language_utils import detect_language, translate_text
from utils.logger import log_error

def main():
    st.set_page_config(
        page_title="Crime Query Assistant",
        page_icon="🔍",
        layout="wide"
    )

    # Custom CSS for better styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .section-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .stButton > button {
        border-radius: 20px;
        height: 2.5rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .clear-button > button {
        background: linear-gradient(90deg, #dc3545 0%, #c82333 100%) !important;
        color: white !important;
    }
    .clear-button > button:hover {
        background: linear-gradient(90deg, #c82333 0%, #a71e2a 100%) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .voice-status {
        background: #e8f5e8;
        padding: 0.5rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .error-status {
        background: #ffe6e6;
        padding: 0.5rem;
        border-radius: 8px;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

    # Main header
    st.markdown("<div class='main-header'>", unsafe_allow_html=True)
    st.title("🔍 Crime Query Assistant")
    st.markdown("**Query crime data using voice or text input in multiple languages**")
    st.markdown("</div>", unsafe_allow_html=True)

    # Sidebar for configuration
    with st.sidebar:
        st.markdown("<div class='section-header'><h3>⚙️ Configuration</h3></div>", unsafe_allow_html=True)

        # STT Engine selection
        stt_engine = st.selectbox(
            "🎤 Speech-to-Text Engine",
            ["google", "whisper"],
            index=0 if config.STT_ENGINE == "google" else 1,
            help="Choose your preferred speech recognition engine"
        )

        # LLM Engine selection
        llm_engine = st.selectbox(
            "🤖 LLM Engine",
            ["ollama", "openai"],
            index=0 if config.LLM_ENGINE == "ollama" else 1,
            help="Select the language model for query parsing"
        )

        # Model name input
        model_name = st.text_input(
            "📝 Model Name",
            value=config.LLM_MODEL_NAME,
            help="Specify the exact model to use"
        )

        # Translation option
        translate_to_english = st.checkbox(
            "🌍 Auto-translate to English",
            value=config.TRANSLATE_TO_ENGLISH,
            help="Automatically translate non-English queries"
        )

        # Results per page
        results_per_page = st.number_input(
            "📄 Results per page",
            min_value=5,
            max_value=100,
            value=10,
            step=5,
            help="Number of results to display per page"
        )

        st.markdown("---")

        # Voice input status
        if hasattr(st.session_state, 'voice_recording') and st.session_state.voice_recording:
            st.markdown("""
            <div class='voice-status'>
                🎤 <strong>Voice Recording Active</strong><br>
                Speak your query now...
            </div>
            """, unsafe_allow_html=True)

        st.markdown("💡 **Tips:**")
        st.markdown("- Use natural language queries")
        st.markdown("- Include dates, locations, and crime types")
        st.markdown("- Voice input supports 12+ languages")
        st.markdown("- Speak clearly and avoid background noise")

    # Main input section
    st.markdown("<div class='section-header'><h3>📝 Query Input</h3></div>", unsafe_allow_html=True)

    # Handle clear button action
    if st.session_state.get('clear_input', False):
        # Clear any relevant session state variables
        if 'query_input' in st.session_state:
            st.session_state.query_input = ""
        if 'voice_text' in st.session_state:
            st.session_state.voice_text = ""
        if 'transcribed_text' in st.session_state:
            st.session_state.transcribed_text = ""
        if 'submitted_query' in st.session_state:
            st.session_state.submitted_query = ""
        if 'page_number' in st.session_state:
            st.session_state.page_number = 1

        # Reset the clear flag
        st.session_state.clear_input = False
        st.rerun()

    # Create input section with clear button
    col_input, col_clear = st.columns([4, 1])

    with col_input:
        # Use the integrated input component
        submitted_query = create_integrated_input_component()

    with col_clear:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some vertical spacing
        if st.button("🗑️ Clear", key="clear_button", help="Clear input and results", use_container_width=True):
            # Reset all relevant session state variables
            keys_to_reset = [
                'current_query',
                'query_input',
                'voice_text',
                'transcribed_text', 
                'submitted_query',
                'pending_voice_text',
                'voice_recording',
                'show_voice_confirmation',
                'voice_submitted_query',
                'voice_auto_submit'
            ]
            
            for key in keys_to_reset:
                if key in st.session_state:
                    if isinstance(st.session_state[key], bool):
                        st.session_state[key] = False
                    elif isinstance(st.session_state[key], (int, float)):
                        st.session_state[key] = 0
                    else:
                        st.session_state[key] = ""
            
            # Reset page number to 1
            st.session_state.page_number = 1
            
            # Clear any stored results
            if 'results' in st.session_state:
                del st.session_state.results
                
            # Force an immediate rerun to refresh the UI
            st.rerun()

    # Alternative approach: Add CSS class to the clear button for custom styling
    st.markdown("""
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const clearButton = document.querySelector('[data-testid="stButton"][title*="Clear"]');
        if (clearButton) {
            clearButton.classList.add('clear-button');
        }
    });
    </script>
    """, unsafe_allow_html=True)

    # Example queries section
    create_example_queries_section()

    # Process query if submitted
    if submitted_query:
        st.markdown("<div class='section-header'><h3>ℹ️ Query Analysis</h3></div>", unsafe_allow_html=True)

        col1, col2 = st.columns([2, 1])

        with col2:
            query_info_placeholder = st.empty()

        with col1:
            try:
                # Detect language
                detected_lang = detect_language(submitted_query)
                st.info(f"🌐 **Detected language:** {detected_lang.upper()}")

                # Translate if needed
                processed_query = submitted_query
                if translate_to_english and detected_lang != 'en':
                    with st.spinner("🔄 Translating query..."):
                        processed_query = translate_text(submitted_query, target_lang='en')
                    st.success(f"🔄 **Translated query:** {processed_query}")

                # Parse query with LLM
                with st.spinner("🤖 Analyzing query with AI..."):
                    if llm_engine == "ollama":
                        parsed_query = parse_query_with_ollama(processed_query, model_name)
                    else:
                        parsed_query = parse_query_with_openai(processed_query, model_name)

                # Handle synonyms
                parsed_query = translate_synonyms(parsed_query)

                # Display query info
                with query_info_placeholder.container():
                    if "error" not in parsed_query:
                        st.markdown("**📋 Parsed Query Components:**")

                        # Display as organized info cards
                        components_found = False

                        if parsed_query.get("crime_category") or parsed_query.get("crime_subcategory"):
                            crime_type = parsed_query.get("crime_category") or parsed_query.get("crime_subcategory")
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>🔍 Crime Category:</strong> <code>{crime_type}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if parsed_query.get("location"):
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>📍 Location:</strong> <code>{parsed_query['location']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if parsed_query.get("date"):
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>📅 Date:</strong> <code>{parsed_query['date']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if parsed_query.get("status"):
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>📊 Status:</strong> <code>{parsed_query['status']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if parsed_query.get("reported_by"):
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>👮 Reported By:</strong> <code>{parsed_query['reported_by']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if parsed_query.get("description"):
                            st.markdown(f"""
                            <div class='info-card'>
                                <strong>📝 Description:</strong> <code>{parsed_query['description']}</code>
                            </div>
                            """, unsafe_allow_html=True)
                            components_found = True

                        if not components_found:
                            st.warning("⚠️ No specific query components identified. Using general search.")

                        # Show raw JSON in expander
                        with st.expander("📄 View Raw Parsed Data"):
                            st.json(parsed_query)
                    else:
                        st.error("❌ Error parsing query")
                        st.json(parsed_query)

                # Build and execute MongoDB query
                if "error" not in parsed_query:
                    mongo_query = build_mongo_query(parsed_query)

                    with st.expander("🗃️ View MongoDB Query"):
                        st.json(mongo_query)

                    # Execute query
                    st.markdown("<div class='section-header'><h3>📊 Query Results</h3></div>", unsafe_allow_html=True)

                    try:
                        with st.spinner("🔍 Searching database..."):
                            results = query_crime_data(mongo_query)

                        if results:
                            total_results = len(results)

                            # Results summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📊 Total Results", total_results)
                            with col2:
                                st.metric("📄 Results per Page", results_per_page)
                            with col3:
                                total_pages = math.ceil(total_results / results_per_page)
                                st.metric("📚 Total Pages", total_pages)

                            # Pagination
                            if 'page_number' not in st.session_state:
                                st.session_state.page_number = 1

                            if total_pages > 1:
                                col_prev, col_info, col_next = st.columns([1, 2, 1])

                                with col_prev:
                                    if st.button("⬅️ Previous", disabled=st.session_state.page_number <= 1):
                                        st.session_state.page_number -= 1
                                        st.rerun()

                                with col_info:
                                    st.markdown(f"**Page {st.session_state.page_number} of {total_pages}**")

                                with col_next:
                                    if st.button("➡️ Next", disabled=st.session_state.page_number >= total_pages):
                                        st.session_state.page_number += 1
                                        st.rerun()

                            # Calculate pagination bounds
                            start_idx = (st.session_state.page_number - 1) * results_per_page
                            end_idx = min(start_idx + results_per_page, total_results)

                            # Display paginated results
                            paginated_results = results[start_idx:end_idx]
                            df = pd.DataFrame(paginated_results)

                            st.dataframe(
                                df,
                                use_container_width=True,
                                height=400
                            )

                            # Show pagination info
                            st.info(f"📋 Showing results {start_idx + 1}-{end_idx} of {total_results}")

                            # Download options
                            st.markdown("### 📥 Download Results")
                            col_csv, col_json = st.columns(2)
                            with col_csv:
                                csv_data = pd.DataFrame(results).to_csv(index=False)
                                st.download_button(
                                    "📊 Download All Results (CSV)",
                                    csv_data,
                                    "crime_query_results.csv",
                                    "text/csv",
                                    use_container_width=True
                                )

                            with col_json:
                                json_data = json.dumps(results, indent=2, ensure_ascii=False)
                                st.download_button(
                                    "📄 Download All Results (JSON)",
                                    json_data,
                                    "crime_query_results.json",
                                    "application/json",
                                    use_container_width=True
                                )
                        else:
                            st.warning("⚠️ No results found for your query.")
                            st.info("""
                            💡 **Suggestions:**
                            - Try different search terms or synonyms
                            - Check if the database contains relevant data
                            - Broaden your date range or location
                            - Use more general terms (e.g., 'theft' instead of 'pickpocketing')
                            """)

                    except Exception as e:
                        st.error(f"❌ Error querying database: {str(e)}")
                        st.info("🔧 Make sure MongoDB is running and the database is populated.")

            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
                log_error(f"Query processing error: {str(e)}")

    else:
        # Show welcome message when no query is submitted, Created using Claude AI
        st.markdown("### 👋 Welcome!")
        st.info("Enter a query above using text input or voice input to search the crime database.")

        st.markdown("### 📖 How to use:")
        st.markdown("""
        **Text Input:**
        - Type your query in the text box and click the send button (📤)

        **Voice Input:**
        - Select your language from the dropdown
        - Click the microphone button (🎤) and speak your query
        - Review the transcribed text and click "Use This" to apply it

        **Clear Data:**
        - Click the red "🗑️ Clear" button to clear the input and reset results

        **Multi-language Support:**
        - Voice input supports 12+ languages including English, Spanish, French, German, Italian, Portuguese, Russian, Japanese, Korean, Chinese, Hindi, and Arabic
        - Text queries are automatically translated to English if needed

        **Sample queries:**
        - "Show me burglaries in downtown last month"  
        - "Robos en Madrid desde enero" (Spanish)
        - "Vol à Paris cette semaine" (French)
        - "Diebstahl in Berlin" (German)
        """)


if __name__ == "__main__":
    main()

#streamlit run main.py --server.address=0.0.0.0 --server.port=8503
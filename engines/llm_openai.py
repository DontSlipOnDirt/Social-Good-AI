from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import json
import re
import os
from dotenv import load_dotenv

load_dotenv()

def parse_query_with_openai(user_query: str, model_name: str = "gpt-3.5-turbo"): # type: ignore
    """
    Parse user query using OpenAI LLM to extract crime query parameters.
    """
    # Use environment variable for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return {"error": "OpenAI API key not found in environment variables"}
    
    llm = ChatOpenAI(model=model_name, openai_api_key=api_key)

    # Prompt needs to be refined further
    # Prompt to LLM, can be changed and needs to be generalized in the future as currently its too specific to the dataset
    prompt_template = ChatPromptTemplate.from_template("""

        You are a multilingual crime data query parser. Your task is to extract structured information from a user query about crime data and return it as a JSON object with the following fields:

        - crime_category: General crime category, normalized to English (e.g., "Theft", "Assault", "Burglary", "Vandalism", "Fraud", "Cybercrime"), but the input may include any language or script, including native names or synonyms. Map these to the English category.
        - crime_subcategory: Specific type or subtype of the crime as mentioned in the query, in the same language or script as used by the user; do not translate unless the query is in English or explicitly asks for English output.
        - location: The city, town, or region mentioned (e.g., "Patna, Bihar", "Matunga, Mumbai, Maharashtra"). Location names may appear in any language or script.
        - date: Date of the crime in ISO format (YYYY-MM-DD) if mentioned; otherwise null.
        - status: Case status if mentioned (normalized to English: "Open", "Closed", "Solved", "Under Investigation"); otherwise null.
        - reported_by: Name or identifier of who reported the crime, in the original script (local or English); include an alternate transliteration only if helpful for matching, but avoid combining both in a single string.
        - description: Brief summary or key details of the incident if present or implied; otherwise null.

        If any field is not mentioned or cannot be determined, assign it a null value.

        User Query:
        {query}

        Respond **only** with a valid JSON object, no additional explanations, formatting, or commentary.

    """)
    
    chain = LLMChain(llm=llm, prompt=prompt_template)
    response = chain.run(query=user_query)
    
    # Extract JSON from response
    try:
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback parsing
            return {"error": "Could not parse LLM response", "raw_response": response}
    except json.JSONDecodeError:
        return {"error": "Invalid JSON in LLM response", "raw_response": response}

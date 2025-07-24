from langchain_community.llms import Ollama
#import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import json
import re

def parse_query_with_ollama(user_query: str, model_name: str = "llama3"): # type: ignore
    """
    Parse user query using Ollama local LLM to extract crime query parameters.
    """
    #llm = Ollama(model=model_name)
    llm = Ollama(model=model_name, base_url="http://localhost:11434")

    # Prompt needs to be refined further
    # Prompt to LLM, can be changed and needs to be generalized in the future as currently its too specific to the dataset
    prompt_template = PromptTemplate(
        input_variables=["query"],
        template="""
        
         You are a multilingual crime data query parser. Extract the following information from the user query and return it as a JSON object:

        - crime_category: General crime category, normalized to English (e.g., "Theft", "Assault", "Burglary", "Vandalism", "Fraud", "Cybercrime"), but the input may include any language or script, including native names or synonyms. Map these to the English category.
        - crime_subcategory: Specific type or subtype of the crime as mentioned in the query, in the same language or script as used by the user; do not translate unless the query is in English or explicitly asks for English output.
        - location: The city, town, or region mentioned (e.g., "Patna, Bihar", "Matunga, Mumbai, Maharashtra"). Location names may appear in any language or script.
        - date: Date of the crime in ISO format (YYYY-MM-DD) if mentioned; otherwise null.
        - status: Case status if mentioned (normalized to English: "Open", "Closed", "Solved", "Under Investigation"); otherwise null.
        - reported_by: Use the name exactly as in the query — do not add transliteration in parentheses or modify the script.
        - description: Brief summary or key details of the incident if present or implied (e.g., who did what, what was stolen); otherwise null.

        If any field is not mentioned or cannot be determined, assign it a null value.

        User Query:
        {query}

        Respond **only** with a valid JSON object, no additional explanations, formatting, or commentary.
        
        """
    )
    
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

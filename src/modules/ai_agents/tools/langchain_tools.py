"""
LangChain Tools for Prescription Processing
Implements the exact tools from the scenario requirements
"""

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.settings.config import settings
from src.core.services.neo4j.rxnorm_rag_service import rxnorm_service
from src.core.settings.logging import logger
import json

# Optional LangFuse import
try:
    from langfuse import observe
except ImportError:
    def observe(name=None, **kwargs):
        def decorator(func):
            return func
        return decorator

# Initialize LangChain models - Use Gemini 2.5 Pro exclusively
llm_vision = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0,
    google_api_key=settings.google_api_key
)

llm_task = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro", 
    temperature=0,
    google_api_key=settings.google_api_key
)

@tool
@observe(name="rxnorm_drug_lookup", as_type="generation", capture_input=True, capture_output=True)
def get_drug_info(drug_name: str, strength: str) -> str:
    """Looks up drug info. Returns a JSON string with keys: 'rxcui', 'ndc', 'drug_schedule', 'brand_drug', 'brand_ndc'."""
    logger.info(f"--- TOOL: Looking up info for {drug_name} {strength} ---")
    
    try:
        # First try Neo4j RxNorm lookup
        rxnorm_result = rxnorm_service.get_drug_info(drug_name, strength)
        if rxnorm_result and len(rxnorm_result) > 0:
            result = rxnorm_result[0]
            return json.dumps({
                "rxcui": result.get("rxcui"),
                "ndc": result.get("ndc"),
                "drug_schedule": result.get("drug_schedule"),
                "brand_drug": result.get("brand_drug"),
                "brand_ndc": result.get("brand_ndc")
            })
    except Exception as e:
        logger.warning(f"Neo4j lookup failed: {e}")
    
    # Fallback to LLM-based lookup
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a pharma database. Return ONLY a valid JSON object string with the exact keys: 'rxcui', 'ndc', 'drug_schedule', 'brand_drug', 'brand_ndc'."),
        ("human", f"Drug: {drug_name}, Strength: {strength}")
    ])
    return (prompt | llm_vision).invoke({}).content

@tool
@observe(name="spanish_translation", as_type="generation", capture_input=True, capture_output=True)
def translate_to_spanish(text: str) -> str:
    """Translates a given single string of text from English to Spanish."""
    logger.info(f"--- TOOL: Translating '{text}' to Spanish ---")
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a professional translator. Translate the following medical instruction from English to Spanish. Return ONLY the Spanish translation as a single string."),
        ("human", text)
    ])
    return (prompt | llm_task).invoke({}).content

@tool
@observe(name="quantity_calculation", as_type="generation", capture_input=True, capture_output=True)
def calculate_quantity(instructions_for_use: str, days_supply: int = 30) -> str:
    """Calculates the total medication quantity needed based on instructions. Only use if quantity is not written."""
    logger.info(f"--- TOOL: Calculating quantity for '{instructions_for_use}' ---")
    prompt = f"A prescription sig is: \"{instructions_for_use}\". Calculate the total quantity for a {days_supply}-day supply. Return ONLY a valid JSON with keys: \"calculated_quantity\" (int) and \"calculation_reasoning\" (str)."
    return llm_task.invoke(prompt).content

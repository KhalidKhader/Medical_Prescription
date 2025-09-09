
from src.core.services.gemini.client import GeminiClient
from google.genai.types import Part, Content
from .prompts import get_drug_parsing_prompt
from src.core.settings.logging import logger
from langfuse import observe
from typing import Dict
import json
from src.modules.ai_agents.utils.json_parser import parse_json

class DrugComponentsAgent:
    def __init__(self):
        self.client = GeminiClient()

    @observe(name="parse_drug_components", as_type="generation", capture_input=True, capture_output=True)
    async def parse_drug_components(self, full_drug_string: str) -> Dict[str, str]:
        """Parse drug string into components using Gemini"""
        try:
            prompt = get_drug_parsing_prompt(full_drug_string)
            contents = [Content(parts=[Part.from_text(prompt)])]
            response = self.client.client.models.generate_content(
                model=self.client.model,
                contents=contents,
                config=self.client.generate_config
            )
            
            return parse_json(response.text.strip()) or {"drug_name": full_drug_string, "strength": "", "form": ""}
        except Exception as e:
            logger.error(f"Drug parsing failed: {e}")
            return {"drug_name": full_drug_string, "strength": "", "form": ""}

from typing import Dict, Any
from google.genai.types import Part, Content
from src.core.services.gemini.client import GeminiClient

client = GeminiClient()

async def gemini_test_connection() -> Dict[str, Any]:
    """Test Gemini connection"""
    try:
        content = Content(
            role="user",
            parts=[Part.from_text("Test connection - respond with 'OK'")]
        )
        
        response = client.client.models.generate_content(
            model=client.model,
            contents=[content],
            config=client.generate_config
        )
        
        # Determine status based on test results
        test_passed = "OK" in response.text
        status = "healthy" if test_passed else "unhealthy"
        
        return {
            "status": status,
            "available": True,
            "model_name": client.model,
            "test_passed": test_passed,
            "response_length": len(response.text),
            "response_text": response.text  # Add for debugging
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "available": False,
            "model_name": client.model,
            "error": str(e)
        }
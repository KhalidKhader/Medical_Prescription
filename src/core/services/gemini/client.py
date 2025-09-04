"""
Gemini Client - Consolidated implementation with processing and models
"""

import base64
import time
from typing import Dict, Any, Optional
from google import genai
from google.genai.types import Part, Content, GenerateContentConfig, SafetySetting
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langfuse import observe
from langfuse import Langfuse
from src.core.settings.config import settings
from src.core.settings.logging import logger


class GeminiClient:
    """Consolidated Gemini client with processing capabilities"""

    def __init__(self):
        """Initialize Gemini client"""
        self.client = genai.Client(api_key=settings.google_api_key)

        # Use Gemini 2.5 Pro as primary model
        self.model = "gemini-2.5-pro"

        # Safety settings for medical applications
        self.safety_settings = [
            SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            ),
            SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_MEDIUM_AND_ABOVE"
            )
        ]

        # Generate content config
        self.generate_config = GenerateContentConfig(
            temperature=0,
            top_p=0.95,
            top_k=40,
            max_output_tokens=8192,
            safety_settings=self.safety_settings
        )

        # Initialize Langfuse
        if settings.langfuse_enabled:
            try:
                self.langfuse = Langfuse(
                    secret_key=settings.langfuse_secret_key,
                    public_key=settings.langfuse_public_key,
                    host=settings.langfuse_host,
                    timeout=settings.langfuse_timeout
                )
            except Exception as e:
                logger.warning(f"LangFuse initialization failed in Gemini client: {e}")
                self.langfuse = None
        else:
            self.langfuse = None

        logger.info("Gemini client initialized with Gemini 2.5 Pro")
    
 

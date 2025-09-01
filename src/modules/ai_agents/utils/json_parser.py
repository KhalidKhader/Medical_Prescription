"""
JSON Parser - Clean JSON parsing with json_repair
Handles extraction and cleaning of JSON from LLM responses
"""

import json
from typing import Dict, Any, Optional
from json_repair import loads as repair_json_loads
from src.core.settings.logging import logger


def clean_json_text(text: str) -> str:
    """
    Clean JSON text by removing common formatting issues
    
    Args:
        text: Raw text that may contain JSON
        
    Returns:
        Cleaned JSON text
    """
    if not text:
        return "{}"
    
    # Remove markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end != -1:
            text = text[start:end]
    elif "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end != -1:
            text = text[start:end]
    
    # Find JSON object boundaries
    text = text.strip()
    
    # Look for first { and last }
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        text = text[first_brace:last_brace + 1]
    
    return text.strip()


def parse_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Parse JSON from text using json_repair for robust parsing
    
    Args:
        text: Text containing JSON
        
    Returns:
        Parsed JSON dictionary or None if parsing fails
    """
    try:
        # Clean the text first
        cleaned_text = clean_json_text(text)
        
        if not cleaned_text:
            return None
        
        # Try standard JSON parsing first
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError:
            # Fall back to json_repair for malformed JSON
            return repair_json_loads(cleaned_text)
            
    except Exception as e:
        logger.error(f"JSON parsing failed: {e}")
        return None


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from mixed text content
    
    Args:
        text: Text that may contain JSON mixed with other content
        
    Returns:
        Extracted JSON dictionary or None
    """
    if not text:
        return None
    
    # Split text into lines and look for JSON-like content
    lines = text.split('\n')
    json_lines = []
    in_json = False
    brace_count = 0
    
    for line in lines:
        stripped = line.strip()
        
        # Check if line contains opening brace
        if '{' in stripped and not in_json:
            in_json = True
            json_lines.append(line)
            brace_count += stripped.count('{') - stripped.count('}')
        elif in_json:
            json_lines.append(line)
            brace_count += stripped.count('{') - stripped.count('}')
            
            # Check if we've closed all braces
            if brace_count <= 0:
                break
    
    if json_lines:
        json_text = '\n'.join(json_lines)
        return parse_json(json_text)
    
    # Fallback: try to parse the entire text
    return parse_json(text)

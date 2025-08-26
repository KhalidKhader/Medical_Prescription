"""
JSON Parser - Clean JSON parsing without regex
Handles extraction and cleaning of JSON from LLM responses
"""

import json
from typing import Dict, Any, Optional, Union
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
            # Fall back to json_repair
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
    # Strategy 3: Extract JSON from mixed content
    extracted_json = extract_json_from_text(text)
    if extracted_json:
        try:
            return json.loads(extracted_json)
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Use json_repair for malformed JSON
    try:
        repaired = json_repair.loads(text)
        if isinstance(repaired, (dict, list)):
            return repaired
        else:
            logger.warning(f"Parsed content is not a valid JSON object (dict or list): {type(repaired)}")
            return None
    except Exception as e:
        logger.error(f"Failed to parse JSON with json_repair: {e}")
    
    # Strategy 5: Try json_repair on cleaned/extracted text
    if cleaned_text or extracted_json:
        for candidate in [cleaned_text, extracted_json]:
            if not candidate:
                continue
            try:
                repaired = json_repair.loads(candidate)
                if isinstance(repaired, (dict, list)):
                    return repaired
            except Exception:
                continue
    
    logger.error(f"All JSON parsing strategies failed for text: {text[:200]}...")
    return None


def clean_json_text(text: str) -> str:
    """
    Clean text before JSON parsing by removing common LLM artifacts.
    Uses string operations instead of regex.
    
    Args:
        text: Raw text that may contain JSON
        
    Returns:
        Cleaned text ready for JSON parsing
    """
    if not text:
        return ""
    
    # Remove markdown code blocks
    if text.startswith('```json'):
        text = text[7:].lstrip('\n')
    if text.startswith('```'):
        text = text[3:].lstrip('\n')
    if text.endswith('```'):
        text = text[:-3].rstrip('\n')
    
    # Remove common LLM prefixes
    prefixes_to_remove = [
        "Here is the JSON:",
        "The JSON is:",
        "JSON:",
        "Here is the",
        "The response is:",
    ]
    
    text_lower = text.lower()
    for prefix in prefixes_to_remove:
        prefix_lower = prefix.lower()
        if prefix_lower in text_lower:
            idx = text_lower.find(prefix_lower)
            if idx != -1:
                # Find the end of the prefix line
                end_idx = idx + len(prefix)
                while end_idx < len(text) and text[end_idx] in ' \t':
                    end_idx += 1
                if end_idx < len(text) and text[end_idx] == '\n':
                    end_idx += 1
                text = text[end_idx:]
                break
    
    # Clean up whitespace
    text = text.strip()
    
    return text


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON content from mixed text using bracket counting.
    No regex - uses character-by-character parsing.
    
    Args:
        text: Text that may contain JSON embedded within other content
        
    Returns:
        Extracted JSON string or None if no JSON found
    """
    if not text:
        return None
    
    # Look for JSON objects starting with {
    for i, char in enumerate(text):
        if char == '{':
            json_str = _extract_balanced_braces(text, i, '{', '}')
            if json_str and _is_likely_json(json_str):
                return json_str
        elif char == '[':
            json_str = _extract_balanced_braces(text, i, '[', ']')
            if json_str and _is_likely_json(json_str):
                return json_str
    
    return None


def _extract_balanced_braces(text: str, start_idx: int, open_char: str, close_char: str) -> Optional[str]:
    """Extract text with balanced braces/brackets."""
    if start_idx >= len(text) or text[start_idx] != open_char:
        return None
    
    count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_idx, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == open_char:
                count += 1
            elif char == close_char:
                count -= 1
                if count == 0:
                    return text[start_idx:i + 1]
    
    return None


def _is_likely_json(text: str) -> bool:
    """Simple heuristic to check if text looks like JSON."""
    text = text.strip()
    if not text:
        return False
    
    # Must start and end with proper JSON delimiters
    if not ((text.startswith('{') and text.endswith('}')) or 
            (text.startswith('[') and text.endswith(']'))):
        return False
    
    # Should contain some JSON-like patterns
    json_indicators = ['":', '":"', '"[', '"]', '"{', '"}', '"null', '"true', '"false']
    return any(indicator in text for indicator in json_indicators)

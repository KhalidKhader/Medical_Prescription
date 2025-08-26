"""
JSON Utilities - High-level JSON processing functions
Combines parsing, validation, and repair functionality
"""

import json
from typing import Dict, Any, Optional, Type, Union
from json_repair import loads as repair_json_loads
from pydantic import BaseModel
from .json_parser import parse_json, extract_json_from_text, clean_json_text
from .json_validator import validate_json_schema, sanitize_json_values
from src.core.settings.logging import logger


def repair_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Repair malformed JSON using json_repair library
    
    Args:
        text: Potentially malformed JSON text
        
    Returns:
        Repaired JSON dictionary or None if repair fails
    """
    try:
        # Clean the text first
        cleaned_text = clean_json_text(text)
        
        if not cleaned_text:
            return None
        
        # Use json_repair to fix malformed JSON
        repaired_data = repair_json_loads(cleaned_text)
        
        # Ensure we return a dictionary
        if isinstance(repaired_data, dict):
            return repaired_data
        elif isinstance(repaired_data, str):
            # Sometimes json_repair returns a string, try parsing again
            return json.loads(repaired_data)
        else:
            logger.warning(f"json_repair returned unexpected type: {type(repaired_data)}")
            return None
            
    except Exception as e:
        logger.error(f"JSON repair failed: {e}")
        return None


def repair_and_validate_json(
    text: str, 
    schema_class: Type[BaseModel]
) -> tuple[bool, Optional[str], Optional[BaseModel], Optional[Dict[str, Any]]]:
    """
    Repair JSON and validate against schema in one step
    
    Args:
        text: JSON text to repair and validate
        schema_class: Pydantic model class for validation
        
    Returns:
        Tuple of (is_valid, error_message, validated_model, raw_data)
    """
    try:
        # First, try to repair the JSON
        repaired_data = repair_json(text)
        
        if repaired_data is None:
            return False, "Failed to parse JSON", None, None
        
        # Sanitize the data
        sanitized_data = sanitize_json_values(repaired_data)
        
        # Validate against schema
        is_valid, error_msg, validated_model = validate_json_schema(
            sanitized_data, schema_class
        )
        
        return is_valid, error_msg, validated_model, sanitized_data
        
    except Exception as e:
        error_msg = f"JSON repair and validation failed: {str(e)}"
        logger.error(error_msg)
        return False, error_msg, None, None


def parse_and_extract_json_field(
    text: str, 
    field_name: str
) -> Optional[Any]:
    """
    Parse JSON and extract a specific field
    
    Args:
        text: JSON text
        field_name: Name of field to extract
        
    Returns:
        Field value or None if not found
    """
    try:
        # Try multiple parsing methods
        data = parse_json(text)
        
        if data is None:
            data = extract_json_from_text(text)
        
        if data is None:
            data = repair_json(text)
        
        if data and isinstance(data, dict):
            return data.get(field_name)
        
        return None
        
    except Exception as e:
        logger.error(f"Failed to extract field '{field_name}': {e}")
        return None


def format_json_for_llm(data: Dict[str, Any]) -> str:
    """
    Format JSON data for LLM consumption
    
    Args:
        data: Dictionary to format
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to format JSON for LLM: {e}")
        return str(data)
    issues = []
    
    # Parse JSON
    parsed_data = parse_json(text)
    if parsed_data is None:
        issues.append("Failed to parse JSON from text")
        return None, issues
    
    if not isinstance(parsed_data, dict):
        issues.append("Parsed data is not a JSON object")
        return None, issues
    
    # Sanitize values
    sanitized_data = sanitize_json_values(parsed_data)
    
    # Validate schema if provided
    if expected_schema:
        required_fields = expected_schema.get("required", [])
        is_valid, missing_fields = validate_json_schema(sanitized_data, required_fields)
        
        if not is_valid:
            issues.extend([f"Missing required field: {field}" for field in missing_fields])
        
        # Add default values for missing optional fields
        default_values = expected_schema.get("defaults", {})
        for field, default_value in default_values.items():
            if field not in sanitized_data:
                sanitized_data[field] = default_value
                issues.append(f"Added default value for field: {field}")
    
    return sanitized_data, issues


def repair_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Simple wrapper for repair_and_validate_json for backward compatibility.
    Returns the repaired JSON data or None if repair fails.
    """
    repaired_data, errors = repair_and_validate_json(text)
    if repaired_data is not None:
        return repaired_data
    else:
        logger.warning(f"JSON repair failed with errors: {errors}")
        return None


def format_json_for_llm(data: Dict[str, Any], indent: int = 2) -> str:
    """
    Format JSON data for LLM consumption with proper indentation.
    
    Args:
        data: Dictionary to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False, sort_keys=True)
    except Exception as e:
        logger.error(f"Failed to format JSON: {e}")
        return str(data)

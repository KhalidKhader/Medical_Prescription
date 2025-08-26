"""
JSON Validator - Schema validation and sanitization
Handles validation of JSON against Pydantic schemas
"""

import json
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError
from src.core.settings.logging import logger


class JSONParsingError(Exception):
    """Custom exception for JSON parsing errors"""
    pass


class JSONValidator:
    """JSON validation utilities"""
    
    @staticmethod
    def validate_json_schema(
        data: Dict[str, Any], 
        schema_class: Type[BaseModel]
    ) -> tuple[bool, Optional[str], Optional[BaseModel]]:
        """
        Validate JSON data against Pydantic schema
        
        Args:
            data: Dictionary to validate
            schema_class: Pydantic model class for validation
            
        Returns:
            Tuple of (is_valid, error_message, validated_model)
        """
        try:
            validated_model = schema_class.parse_obj(data)
            return True, None, validated_model
        except ValidationError as e:
            error_msg = str(e)
            logger.error(f"Schema validation failed: {error_msg}")
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, None
    
    @staticmethod
    def sanitize_json_values(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize JSON values by removing invalid characters and normalizing
        
        Args:
            data: Dictionary to sanitize
            
        Returns:
            Sanitized dictionary
        """
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            clean_key = key.strip() if isinstance(key, str) else key
            
            # Sanitize value
            if isinstance(value, str):
                # Clean string values
                clean_value = value.strip()
                # Convert empty strings to None
                clean_value = None if clean_value == "" else clean_value
            elif isinstance(value, dict):
                # Recursively sanitize nested dictionaries
                clean_value = JSONValidator.sanitize_json_values(value)
            elif isinstance(value, list):
                # Sanitize list items
                clean_value = [
                    JSONValidator.sanitize_json_values(item) 
                    if isinstance(item, dict) 
                    else item 
                    for item in value
                ]
            else:
                clean_value = value
            
            sanitized[clean_key] = clean_value
        
        return sanitized


def validate_json_schema(
    data: Dict[str, Any], 
    schema_class: Type[BaseModel]
) -> tuple[bool, Optional[str], Optional[BaseModel]]:
    """
    Convenience function for schema validation
    
    Args:
        data: Dictionary to validate
        schema_class: Pydantic model class
        
    Returns:
        Tuple of (is_valid, error_message, validated_model)
    """
    return JSONValidator.validate_json_schema(data, schema_class)


def sanitize_json_values(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function for value sanitization
    
    Args:
        data: Dictionary to sanitize
        
    Returns:
        Sanitized dictionary
    """
    return JSONValidator.sanitize_json_values(data)
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, dict):
            sanitized[key] = sanitize_json_values(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_json_values(item) if isinstance(item, dict) else item for item in value]
        elif value is None:
            sanitized[key] = None
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        else:
            # Convert everything else to string
            sanitized[key] = str(value)
    
    return sanitized


class JSONValidator:
    """Class for advanced JSON validation with custom rules"""
    
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.required_fields = schema.get("required", [])
        self.field_types = schema.get("types", {})
        self.field_validators = schema.get("validators", {})
    
    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data against the schema.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        is_valid, missing_fields = validate_json_schema(data, self.required_fields)
        if not is_valid:
            errors.extend([f"Missing required field: {field}" for field in missing_fields])
        
        # Check field types
        for field, expected_type in self.field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    errors.append(f"Field '{field}' should be of type {expected_type.__name__}, got {type(data[field]).__name__}")
        
        # Run custom validators
        for field, validator_func in self.field_validators.items():
            if field in data:
                try:
                    is_field_valid = validator_func(data[field])
                    if not is_field_valid:
                        errors.append(f"Field '{field}' failed custom validation")
                except Exception as e:
                    errors.append(f"Validation error for field '{field}': {str(e)}")
        
        return len(errors) == 0, errors


class JSONParsingError(Exception):
    """Custom exception for JSON parsing errors"""
    def __init__(self, message: str, original_text: str = "", attempted_repairs: List[str] = None):
        super().__init__(message)
        self.original_text = original_text
        self.attempted_repairs = attempted_repairs or []

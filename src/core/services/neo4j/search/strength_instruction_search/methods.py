from typing import Dict, Any
from src.core.settings.config import settings

def extract_strength_numbers(strength: str) -> str:
    """Extract numeric part of strength for comparison"""
    if not strength:
        return ""
    # Extract digits and decimal points
    numeric_part = ''.join(c for c in strength if c.isdigit() or c == '.')
    return numeric_part.strip('.').lstrip('0') if numeric_part else ""

def normalize_strength(strength: str) -> str:
    """Normalize strength for better matching"""
    if not strength:
        return ""
    # Extract the numeric part
    numeric_part = extract_strength_numbers(strength)
    # Remove leading zeros and trailing dots
    if numeric_part:
        numeric_part = numeric_part.strip('.').lstrip('0')
        if not numeric_part:
            numeric_part = "0"
    return numeric_part

def analyze_comprehensive_context(prescription_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze all prescription data for comprehensive search context"""
    context = {
        "drug_variants": [],
        "strength_filters": [],
        "route_filters": [],
        "form_filters": [],
        "brand_generic_hints": []
    }
    
    drug_name = prescription_data.get("drug_name", "")
    strength = prescription_data.get("strength", "")
    instructions = prescription_data.get("instructions", "")
    synonyms = prescription_data.get("synonyms", [])
    
    # Drug name variants
    context["drug_variants"] = [drug_name.lower()]
    if synonyms:
        context["drug_variants"].extend([s.lower() for s in synonyms])
    
    # Strength context
    if strength:
        strength_num = extract_strength_numbers(strength)
        if strength_num:
            context["strength_filters"] = [
                f"CONTAINS '{strength_num}'",
                f"CONTAINS '{strength.lower()}'",
                f"= '{strength.lower()}'"
            ]
    
    # Route and form analysis from instructions
    if instructions:
        inst_lower = instructions.lower()
        
        # Route analysis
        if any(word in inst_lower for word in ['oral', 'po', 'by mouth', 'swallow', 'take']):
            context["route_filters"].append("oral")
        if any(word in inst_lower for word in ['eye', 'ophthalmic', 'ou', 'od', 'os', 'instill']):
            context["route_filters"].append("ophthalmic")
        if any(word in inst_lower for word in ['ear', 'otic', 'au', 'ad', 'as']):
            context["route_filters"].append("otic")
        if any(word in inst_lower for word in ['topical', 'apply', 'skin']):
            context["route_filters"].append("topical")
        if any(word in inst_lower for word in ['nasal', 'nose', 'nostril']):
            context["route_filters"].append("nasal")
        if any(word in inst_lower for word in ['inhale', 'inhalation', 'puff']):
            context["route_filters"].append("inhalation")
        
        # Form analysis
        if any(word in inst_lower for word in ['tablet', 'tab']):
            context["form_filters"].append("tablet")
        if any(word in inst_lower for word in ['capsule', 'cap']):
            context["form_filters"].append("capsule")
        if any(word in inst_lower for word in ['drop', 'drops', 'gtt', 'gtts']):
            context["form_filters"].append("drops")
            context["form_filters"].append("solution")
        if any(word in inst_lower for word in ['cream', 'ointment', 'gel']):
            context["form_filters"].append("cream")
            context["form_filters"].append("ointment")
        if any(word in inst_lower for word in ['injection', 'inject']):
            context["form_filters"].append("injection")
        if any(word in inst_lower for word in ['inhaler', 'spray']):
            context["form_filters"].append("inhaler")
        if any(word in inst_lower for word in ['liquid', 'solution', 'syrup']):
            context["form_filters"].append("solution")
            context["form_filters"].append("liquid")
    
    return context
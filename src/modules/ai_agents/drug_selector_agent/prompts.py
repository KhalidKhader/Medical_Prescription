from typing import Dict, Any, List

def build_drug_selection_prompt(
        candidates: List[Dict[str, Any]], 
        original_medication: Dict[str, Any]
    ) -> str:
        """Build prompt for drug selection focusing on avoiding wrong suffixes"""
        
        original_drug = original_medication.get("drug_name", "")
        original_strength = original_medication.get("strength", "")
        original_instructions = original_medication.get("instructions_for_use", "")
        
        candidates_text = ""
        for i, candidate in enumerate(candidates[:8]):
            candidates_text += f"""
                Option {i+1}:
                - RXCUI: {candidate.get('rxcui', 'N/A')}
                - Name: {candidate.get('drug_name', 'Unknown')}
                - Generic: {candidate.get('generic_name', 'N/A')}
                - Strength: {candidate.get('strength', 'N/A')}
                - Route: {candidate.get('route', 'N/A')}
                - Dose Form: {candidate.get('dose_form', 'N/A')}
                - Term Type: {candidate.get('term_type', 'N/A')}
            """
        
        return f"""
            You are an expert clinical pharmacist selecting the most appropriate drug match from RxNorm.

            ORIGINAL PRESCRIPTION:
            - Drug Name: "{original_drug}"
            - Strength: "{original_strength}"
            - Instructions: "{original_instructions}"

            AVAILABLE OPTIONS:{candidates_text}

            CRITICAL SELECTION RULES:
            1. **AVOID WRONG SUFFIXES**: Do NOT select "chewable", "rapid disintegrating", "extended release", etc. unless explicitly ordered
            2. **EXACT STRENGTH MATCH**: Prioritize exact strength matches over approximate
            3. **APPROPRIATE FORM**: Match the intended dosage form (tablet vs capsule vs liquid)
            4. **ROUTE COMPATIBILITY**: Ensure route matches instructions (oral vs topical vs ophthalmic)
            5. **BRAND/GENERIC ACCURACY**: Prefer exact brand or generic name matches

            SELECTION PRIORITY:
            1. Exact drug name + exact strength + appropriate form
            2. Generic equivalent + exact strength + appropriate form  
            3. Brand equivalent + exact strength + appropriate form
            4. Close match with compatible strength and form

            Return ONLY valid JSON:
            {{
                "selected_rxcui": "best matching RXCUI",
                "selected_drug_name": "selected drug name",
                "selection_reason": "why this option was selected",
                "avoided_issues": "any wrong suffixes or forms avoided",
                "confidence": 85
            }}
        """

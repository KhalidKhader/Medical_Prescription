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
        for i, candidate in enumerate(candidates[:15]): # Show top 15 candidates
            candidates_text += f"""
                Option {i+1}:
                - RXCUI: {candidate.get('rxcui', 'N/A')}
                - Name: {candidate.get('drug_name', 'Unknown')}
                - Generic Name: {candidate.get('generic_name', 'N/A')}
                - Strength: {candidate.get('strength', 'N/A')}
                - Form: {candidate.get('dose_form', 'N/A')}
                - Search Method: {candidate.get('search_method', 'N/A')}
                - Score: {candidate.get('comprehensive_score', 'N/A')}
            """
        
        return f"""
            You are an expert clinical pharmacist tasked with selecting the most accurate medication from a list of candidates based on a prescription. Your decision must be precise and clinically sound.

            **Original Prescription Details:**
            - **Drug Name**: "{original_drug}" (This could be a brand name, generic name, or a misspelling)
            - **Strength**: "{original_strength}"
            - **Instructions**: "{original_instructions}"

            **Available Drug Candidates from RxNorm:**
            {candidates_text}

            **CRITICAL SELECTION CRITERIA (in order of importance):**
            1.  **Strength Match**: This is the highest priority. The selected drug's strength MUST EXACTLY match the prescribed strength. Do not select a drug with the wrong strength, even if the name is a perfect match.
            2.  **Name Relevance**: The selected drug name should be the most plausible match. Consider that the original may be a brand name and the best match is a generic, or vice-versa.
            3.  **Dosage Form Consistency**: The form (e.g., Tablet, Capsule, Cream) should be consistent with the instructions.
            4.  **Search Method Confidence**: Candidates found through more reliable methods like 'exact_match' or 'brand_exact' are generally preferred over 'fuzzy_match' or 'embedding_search', but only if the strength and form are correct.
            5.  **Comprehensive Score**: Use the score as a guide, but do not rely on it exclusively. Your clinical judgment on the above criteria is more important.

            **Your Task:**
            Review the candidates and select the single best match.

            Return ONLY a valid JSON object with your selection:
            {{
                "selected_rxcui": "The RXCUI of the best matching drug",
                "selection_reason": "A brief, clear justification for your choice, explicitly mentioning why it's superior to other options (e.g., 'Selected Ibuprofen for exact 800mg strength match over Motrin 200mg').",
                "confidence_score": "A score from 0 to 100 indicating your confidence in this selection."
            }}
        """
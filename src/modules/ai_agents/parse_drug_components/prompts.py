def get_drug_parsing_prompt(full_drug_string: str) -> str:
    return f"""Extract the following fields from this medication string. CRITICAL: Preserve the original drug name exactly as written - do not substitute or change drug names.

- drug_name: The base name of the medication without strength or dosage form (preserve original spelling exactly)
- strength: The strength/dose (e.g., "1000 MG", "25mg", "100units/ml")  
- form: The dosage form (e.g., "Oral", "Tablet", "Solution for Injection")

Medication string: "{full_drug_string}"

IMPORTANT: Keep the drug name exactly as provided. Do not change "Anaprox" to "Amoxil" or "Keflex" to "KEPPRA" - preserve the original name.

Return JSON only:
{{
    "drug_name": "extracted_name",
    "strength": "extracted_strength", 
    "form": "extracted_form"
}}"""
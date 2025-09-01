"""
Spanish Translation Agent Prompts
Contains prompts for translating medication instructions to Spanish
"""


def get_spanish_translation_prompt(sig_english: str) -> str:
    """
    Get prompt for translating medication instructions to Spanish
    
    Args:
        sig_english: English instructions to translate
        
    Returns:
        Translation prompt
    """
    return f"""
You are a pharmacy intern working under a supervising pharmacist. Translate the following medical instruction from English to Spanish for pharmacist review.

English Instruction to Translate:
"{sig_english}"

TRANSLATION REQUIREMENTS:
- Use clear, patient-friendly Spanish
- NO ACCENTS on any letters (á→a, é→e, í→i, ó→o, ú→u, ñ→n)
- Maintain medical accuracy
- Use standard medical terminology
- Ensure translation is easily understood by patients
- Follow same structure as English version

Return ONLY the Spanish translation as a single string.

Examples:
- "Take 1 tablet by mouth twice daily" → "Tome 1 tableta por via oral dos veces al dia"
- "Give 2 puffs by inhalation twice daily" → "Give 2 inhalaciones por inhalacion dos veces al dia"
- "Apply twice daily as needed" → "Aplique dos veces al dia segun sea necesario"
"""
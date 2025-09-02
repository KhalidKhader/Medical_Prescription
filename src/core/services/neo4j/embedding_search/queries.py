search_by_embedding = """
MATCH (d:Drug) 
WHERE d.embedding IS NOT NULL 
RETURN d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
        d.generic_name as generic_name, d.strength as strength, d.route as route,
        d.dose_form as dose_form, d.term_type as term_type, d.embedding as embedding
LIMIT 1000
"""

def search_by_embedding_with_strength(strength_filter) -> str:
    return f"""
                MATCH (d:Drug) 
                WHERE d.embedding IS NOT NULL {strength_filter}
                RETURN d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type, d.embedding as embedding
                LIMIT 1000
                """
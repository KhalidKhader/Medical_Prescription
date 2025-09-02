search_fuzzy_drug_name = """
                MATCH (d:Drug)
                WHERE toLower(d.name) CONTAINS toLower($drug_name)
                   OR toLower(d.full_name) CONTAINS toLower($drug_name)
                   OR toLower($drug_name) CONTAINS toLower(d.name)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type,
                       CASE 
                         WHEN toLower(d.name) CONTAINS toLower($drug_name) THEN 0.9
                         WHEN toLower(d.full_name) CONTAINS toLower($drug_name) THEN 0.8
                         WHEN toLower($drug_name) CONTAINS toLower(d.name) THEN 0.7
                         ELSE 0.6
                       END as match_confidence
                ORDER BY match_confidence DESC
                LIMIT $limit
                """


search_fuzzy_with_strength = """
                MATCH (d:Drug)
                WHERE (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.full_name) CONTAINS toLower($drug_name))
                  AND (toLower(d.strength) CONTAINS toLower($strength) OR $strength = "")
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type,
                       CASE 
                         WHEN toLower(d.name) CONTAINS toLower($drug_name) AND toLower(d.strength) CONTAINS toLower($strength) THEN 0.95
                         WHEN toLower(d.name) CONTAINS toLower($drug_name) THEN 0.8
                         WHEN toLower(d.full_name) CONTAINS toLower($drug_name) AND toLower(d.strength) CONTAINS toLower($strength) THEN 0.85
                         WHEN toLower(d.full_name) CONTAINS toLower($drug_name) THEN 0.7
                         ELSE 0.6
                       END as match_confidence
                ORDER BY match_confidence DESC
                LIMIT $limit
                """

def search_word_overlap(word_clause) -> str:
    return f"""
            MATCH (d:Drug)
            WHERE {word_clause}
            RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                    d.generic_name as generic_name, d.strength as strength, d.route as route,
                    d.dose_form as dose_form, d.term_type as term_type
            LIMIT $limit
            """
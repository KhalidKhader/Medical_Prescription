search_synonym_in_rxnorm_query ="""
                MATCH (d:Drug)
                WHERE toLower(d.name) = toLower($synonym)
                   OR toLower(d.full_name) = toLower($synonym)
                   OR toLower(d.name) CONTAINS toLower($synonym)
                   OR toLower(d.full_name) CONTAINS toLower($synonym)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type,
                       CASE 
                         WHEN toLower(d.name) = toLower($synonym) THEN 0.95
                         WHEN toLower(d.full_name) = toLower($synonym) THEN 0.9
                         WHEN toLower(d.name) CONTAINS toLower($synonym) THEN 0.8
                         WHEN toLower(d.full_name) CONTAINS toLower($synonym) THEN 0.75
                         ELSE 0.7
                       END as match_confidence
                ORDER BY match_confidence DESC
                LIMIT $limit
                """

search_synonym_with_strength_in_rxnorm_query = """
                MATCH (d:Drug)
                WHERE (toLower(d.name) CONTAINS toLower($synonym) OR toLower(d.full_name) CONTAINS toLower($synonym))
                  AND toLower(d.strength) CONTAINS toLower($strength)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type,
                       CASE 
                         WHEN toLower(d.name) CONTAINS toLower($synonym) AND toLower(d.strength) CONTAINS toLower($strength) THEN 0.95
                         WHEN toLower(d.full_name) CONTAINS toLower($synonym) AND toLower(d.strength) CONTAINS toLower($strength) THEN 0.9
                         ELSE 0.8
                       END as match_confidence
                ORDER BY match_confidence DESC
                LIMIT $limit
                """
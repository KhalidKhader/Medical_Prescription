def strength_instruction_search(drug_clause, strength_clause, route_clause, form_clause) -> str:
    return f"""
    MATCH (d:Drug)
    WHERE ({drug_clause}){strength_clause}{route_clause}{form_clause}
    RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
            d.generic_name as generic_name, d.strength as strength, d.route as route,
            d.dose_form as dose_form, d.term_type as term_type,
            CASE 
                WHEN toLower(d.strength) CONTAINS toLower($target_strength) THEN 10
                WHEN toLower(d.route) CONTAINS toLower($target_route) THEN 8
                WHEN toLower(d.dose_form) CONTAINS toLower($target_form) THEN 6
                ELSE 4
            END as context_score
    ORDER BY context_score DESC, d.term_type
    LIMIT $limit
    """
def strength_focused_search(drug_clause, strength_clause) -> str:
    return f"""
    MATCH (d:Drug)
    WHERE ({drug_clause})
        AND ({strength_clause})
    RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
            d.generic_name as generic_name, d.strength as strength, d.route as route,
            d.dose_form as dose_form, d.term_type as term_type,
            CASE
                WHEN toLower(d.strength) CONTAINS $normalized_strength THEN 25
                WHEN toLower(d.strength) CONTAINS toLower($full_strength) THEN 20
                ELSE 15
            END as strength_score
    ORDER BY strength_score DESC, d.term_type
    LIMIT $limit
    """
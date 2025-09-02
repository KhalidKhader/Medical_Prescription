search_by_route = """
MATCH (d:Drug)
WHERE (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.full_name) CONTAINS toLower($drug_name))
    AND toLower(d.route) CONTAINS toLower($route_hint)
RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
        d.generic_name as generic_name, d.strength as strength, d.route as route,
        d.dose_form as dose_form, d.term_type as term_type
LIMIT $limit
"""

search_by_form = """
MATCH (d:Drug)
WHERE (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.full_name) CONTAINS toLower($drug_name))
    AND toLower(d.dose_form) CONTAINS toLower($form_hint)
RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
        d.generic_name as generic_name, d.strength as strength, d.route as route,
        d.dose_form as dose_form, d.term_type as term_type
LIMIT $limit
"""

search_by_route_and_strength = """
                MATCH (d:Drug)
                WHERE (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.full_name) CONTAINS toLower($drug_name))
                  AND toLower(d.route) CONTAINS toLower($route_hint)
                  AND toLower(d.strength) CONTAINS toLower($strength)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type
                LIMIT $limit
                """

search_by_form_and_strength = """
                MATCH (d:Drug)
                WHERE (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.full_name) CONTAINS toLower($drug_name))
                  AND toLower(d.dose_form) CONTAINS toLower($form_hint)
                  AND toLower(d.strength) CONTAINS toLower($strength)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type
                LIMIT $limit
                """
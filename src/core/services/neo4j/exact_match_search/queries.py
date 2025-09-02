search_exact_drug_name = """
                MATCH (d:Drug)
                WHERE toLower(d.name) = toLower($drug_name)
                   OR toLower(d.full_name) = toLower($drug_name)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type
                LIMIT $limit
                """

search_exact_with_strength = """
                MATCH (d:Drug)
                WHERE (toLower(d.name) = toLower($drug_name) OR toLower(d.full_name) = toLower($drug_name))
                  AND toLower(d.strength) CONTAINS toLower($strength)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type
                LIMIT $limit
                """
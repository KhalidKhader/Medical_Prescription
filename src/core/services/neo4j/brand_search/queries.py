
search_brand_exact="""
                MATCH (d:Drug)
                WHERE d.term_type IN ['SBD', 'BPCK', 'SCD', 'GPCK']
                  AND (toLower(d.name) = toLower($drug_name) 
                       OR toLower(d.full_name) = toLower($drug_name)
                       OR toLower(d.sxdg_name) = toLower($drug_name))
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type, d.sxdg_name as brand_name
                ORDER BY 
                  CASE d.term_type 
                    WHEN 'SBD' THEN 1 
                    WHEN 'BPCK' THEN 2 
                    WHEN 'SCD' THEN 3 
                    WHEN 'GPCK' THEN 4 
                    ELSE 5 
                  END
                LIMIT $limit
                """


search_brand_fuzzy="""
                MATCH (d:Drug)
                WHERE d.term_type IN ['SBD', 'BPCK', 'SCD', 'GPCK']
                  AND (toLower(d.name) CONTAINS toLower($drug_name)
                       OR toLower(d.full_name) CONTAINS toLower($drug_name)
                       OR toLower(d.sxdg_name) CONTAINS toLower($drug_name)
                       OR toLower($drug_name) CONTAINS toLower(d.name))
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type, d.sxdg_name as brand_name,
                       CASE 
                         WHEN toLower(d.name) CONTAINS toLower($drug_name) THEN 0.9
                         WHEN toLower(d.full_name) CONTAINS toLower($drug_name) THEN 0.85
                         WHEN toLower(d.sxdg_name) CONTAINS toLower($drug_name) THEN 0.8
                         WHEN toLower($drug_name) CONTAINS toLower(d.name) THEN 0.75
                         ELSE 0.7
                       END as match_confidence
                ORDER BY match_confidence DESC,
                  CASE d.term_type 
                    WHEN 'SBD' THEN 1 
                    WHEN 'BPCK' THEN 2 
                    WHEN 'SCD' THEN 3 
                    WHEN 'GPCK' THEN 4 
                    ELSE 5 
                  END
                LIMIT $limit
                """

search_generic_to_brand="""
                MATCH (d:Drug)
                WHERE d.term_type IN ['SBD', 'BPCK']
                  AND (toLower(d.name) CONTAINS toLower($generic_name)
                       OR toLower(d.full_name) CONTAINS toLower($generic_name)
                       OR toLower(d.generic_name) CONTAINS toLower($generic_name))
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type, d.sxdg_name as brand_name
                ORDER BY d.term_type
                LIMIT $limit
                """
search_brand_with_strength = """
                MATCH (d:Drug)
                WHERE d.term_type IN ['SBD', 'BPCK', 'SCD', 'GPCK']
                  AND (toLower(d.name) CONTAINS toLower($drug_name) OR toLower(d.sxdg_name) CONTAINS toLower($drug_name))
                  AND toLower(d.strength) CONTAINS toLower($strength)
                RETURN DISTINCT d.rxcui as rxcui, d.name as drug_name, d.full_name as full_name,
                       d.generic_name as generic_name, d.strength as strength, d.route as route,
                       d.dose_form as dose_form, d.term_type as term_type, d.sxdg_name as brand_name
                ORDER BY 
                  CASE d.term_type 
                    WHEN 'SBD' THEN 1 
                    WHEN 'BPCK' THEN 2 
                    WHEN 'SCD' THEN 3 
                    WHEN 'GPCK' THEN 4 
                    ELSE 5 
                  END
                LIMIT $limit
                """


"""
Neo4j Cypher queries for RxNorm Knowledge Graph.
Contains all database queries for drug information retrieval.
"""

from typing import Dict, Any

# Health check and sample queries
HEALTH_CHECK_QUERY = """
MATCH (c:Concept)
WITH count(c) as total_concepts
MATCH (a:Attribute)
WITH total_concepts, count(a) as total_attributes
MATCH (s:Source)
WITH total_concepts, total_attributes, count(s) as total_sources
MATCH (st:SemanticType)
RETURN total_concepts, total_attributes, total_sources, count(st) as total_semantic_types
"""

SAMPLE_DRUG_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS 'aspirin'
RETURN d.rxcui as concept_id, d.name as drug_name
LIMIT 1
"""

DRUG_SEARCH_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS toLower($drug_name)
OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
RETURN 
    d.rxcui as concept_id, 
    d.name as concept_name,
    d.name as drug_name,
    n.ndc as ndc,
    sch.schedule as drug_schedule,
    b.name as brand_drug,
    b.ndc as brand_ndc
ORDER BY d.name
LIMIT $limit
"""

EXACT_DRUG_MATCH_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) = toLower($drug_name)
RETURN d.rxcui as concept_id, d.name as drug_name
LIMIT 1
"""

DRUG_DETAILS_QUERY = """
MATCH (d:Drug {rxcui: $concept_id})
OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
RETURN 
    'NDC' as attribute_type, n.ndc as attribute_value
UNION ALL
MATCH (d:Drug {rxcui: $concept_id})-[:HAS_SCHEDULE]->(sch:Schedule)
RETURN 
    'DEA_SCHEDULE' as attribute_type, sch.schedule as attribute_value
UNION ALL
MATCH (d:Drug {rxcui: $concept_id})-[:HAS_BRAND]->(b:Brand)
RETURN 
    'BRAND_NAME' as attribute_type, b.name as attribute_value
UNION ALL
MATCH (d:Drug {rxcui: $concept_id})-[:HAS_BRAND]->(b:Brand)
RETURN 
    'BRAND_NDC' as attribute_type, b.ndc as attribute_value
"""

NDC_LOOKUP_QUERY = """
MATCH (n:NDC {ndc: $ndc_code})<-[:HAS_NDC]-(d:Drug)
RETURN d.rxcui as concept_id, d.name as drug_name
LIMIT 1
"""

FLEXIBLE_QUERY = """
MATCH (c:Concept)
WHERE toLower(coalesce(c.str, c.name, c.conceptName, '')) CONTAINS toLower($drug_name)
OPTIONAL MATCH (c)-[r]->(related)
WHERE type(r) IN ['has_tradename', 'ingredient_of', 'has_dose_form', 'HAS_ATTRIBUTE']
RETURN 
    coalesce(c.rxcui, c.conceptId) as rxcui,
    coalesce(c.str, c.name, c.conceptName) as drug_name,
    c.tty as term_type,
    collect(DISTINCT coalesce(related.str, related.name, related.attributeValue)) as related_terms
ORDER BY 
    CASE 
        WHEN toLower(coalesce(c.str, c.name, c.conceptName, '')) = toLower($drug_name) THEN 1
        WHEN toLower(coalesce(c.str, c.name, c.conceptName, '')) STARTS WITH toLower($drug_name) THEN 2
        ELSE 3
    END
LIMIT 10
"""

FUZZY_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS toLower($drug_name)
    OR toLower(d.name) =~ toLower($pattern)
RETURN d.rxcui as concept_id, d.name as drug_name, d.name as concept_name,
        null as ndc, null as drug_schedule, null as brand_drug, null as brand_ndc
ORDER BY 
    CASE WHEN toLower(d.name) = toLower($drug_name) THEN 0 
            WHEN toLower(d.name) STARTS WITH toLower($drug_name) THEN 1
            ELSE 2 END,
    d.name
LIMIT $limit
"""


class RxNormQueries:
    """Collection of Neo4j Cypher queries for RxNorm operations"""
    
    def get_drug_by_name_query(self) -> str:
        """Query to find drug by name with optional strength matching"""
        return """
        MATCH (d:Drug)
        WHERE toLower(d.name) CONTAINS $drug_name
        OPTIONAL MATCH (d)-[:HAS_STRENGTH]->(s:Strength)
        OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            d.dosage_form as dosage_form,
            d.route as route,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            b.name as brand_drug,
            b.ndc as brand_ndc,
            d.manufacturer as manufacturer
        ORDER BY 
            CASE 
                WHEN toLower(d.name) = $drug_name THEN 1
                WHEN toLower(d.name) STARTS WITH $drug_name THEN 2
                ELSE 3
            END,
            CASE 
                WHEN $strength = '' THEN 1
                WHEN toLower(d.strength) CONTAINS toLower($strength) THEN 1
                ELSE 2
            END
        LIMIT $limit
        """
    
    def get_fuzzy_drug_search_query(self) -> str:
        """Fuzzy search query for drug names using soundex or similar"""
        return """
        MATCH (d:Drug)
        WHERE toLower(d.name) CONTAINS $drug_name
        OR apoc.text.levenshteinSimilarity(toLower(d.name), $drug_name) > 0.7
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            b.name as brand_drug,
            b.ndc as brand_ndc,
            apoc.text.levenshteinSimilarity(toLower(d.name), $drug_name) as similarity
        ORDER BY similarity DESC
        LIMIT $limit
        """
    
    def get_drug_by_rxcui_query(self) -> str:
        """Query to get complete drug information by RxCUI"""
        return """
        MATCH (d:Drug {rxcui: $rxcui})
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
        OPTIONAL MATCH (d)-[:HAS_INGREDIENT]->(i:Ingredient)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            d.dosage_form as dosage_form,
            d.route as route,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            b.name as brand_drug,
            b.ndc as brand_ndc,
            d.manufacturer as manufacturer,
            collect(i.name) as ingredients
        """
    
    def get_drug_interactions_query(self) -> str:
        """Query to find drug interactions between multiple RxCUIs"""
        return """
        MATCH (d1:Drug)-[:INTERACTS_WITH]->(d2:Drug)
        WHERE d1.rxcui IN $rxcui_list AND d2.rxcui IN $rxcui_list
        OPTIONAL MATCH (interaction:Interaction)-[:BETWEEN]->(d1)
        OPTIONAL MATCH (interaction)-[:BETWEEN]->(d2)
        RETURN 
            d1.rxcui as drug1_rxcui,
            d1.name as drug1_name,
            d2.rxcui as drug2_rxcui,
            d2.name as drug2_name,
            interaction.severity as severity,
            interaction.description as description,
            interaction.mechanism as mechanism
        ORDER BY 
            CASE interaction.severity
                WHEN 'Major' THEN 1
                WHEN 'Moderate' THEN 2
                WHEN 'Minor' THEN 3
                ELSE 4
            END
        """
    
    def get_brand_to_generic_query(self) -> str:
        """Query to find generic equivalent of brand drug"""
        return """
        MATCH (b:Brand {name: $brand_name})<-[:HAS_BRAND]-(d:Drug)
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            b.name as brand_drug,
            b.ndc as brand_ndc
        """
    
    def get_drug_by_ndc_query(self) -> str:
        """Query to find drug by NDC code"""
        return """
        MATCH (n:NDC {ndc: $ndc})<-[:HAS_NDC]-(d:Drug)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            d.dosage_form as dosage_form,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            b.name as brand_drug,
            b.ndc as brand_ndc
        """
    
    def get_controlled_substances_query(self) -> str:
        """Query to find all controlled substances"""
        return """
        MATCH (d:Drug)-[:HAS_SCHEDULE]->(sch:Schedule)
        WHERE sch.schedule IN ['I', 'II', 'III', 'IV', 'V']
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            n.ndc as ndc,
            sch.schedule as drug_schedule
        ORDER BY sch.schedule, d.name
        LIMIT $limit
        """
    
    def get_drug_synonyms_query(self) -> str:
        """Query to find drug synonyms and alternative names"""
        return """
        MATCH (d:Drug {rxcui: $rxcui})-[:HAS_SYNONYM]->(s:Synonym)
        RETURN collect(s.name) as synonyms
        """
    
    def get_dosage_forms_query(self) -> str:
        """Query to get available dosage forms for a drug"""
        return """
        MATCH (d:Drug)
        WHERE toLower(d.name) CONTAINS toLower($drug_name)
        RETURN DISTINCT d.dosage_form as dosage_form
        ORDER BY d.dosage_form
        """
    
    def get_drug_routes_query(self) -> str:
        """Query to get available routes for a drug"""
        return """
        MATCH (d:Drug)
        WHERE toLower(d.name) CONTAINS toLower($drug_name)
        RETURN DISTINCT d.route as route
        ORDER BY d.route
        """
    
    def search_drugs_by_indication_query(self) -> str:
        """Query to find drugs by indication/condition"""
        return """
        MATCH (d:Drug)-[:INDICATED_FOR]->(c:Condition)
        WHERE toLower(c.name) CONTAINS toLower($indication)
        OPTIONAL MATCH (d)-[:HAS_NDC]->(n:NDC)
        OPTIONAL MATCH (d)-[:HAS_SCHEDULE]->(sch:Schedule)
        RETURN 
            d.rxcui as rxcui,
            d.name as generic_name,
            d.strength as strength,
            n.ndc as ndc,
            sch.schedule as drug_schedule,
            c.name as indication
        ORDER BY d.name
        LIMIT $limit
        """
    
    def get_database_stats_query(self) -> str:
        """Query to get RxNorm database statistics"""
        return """
        MATCH (d:Drug)
        WITH count(d) as total_drugs
        MATCH (n:NDC)
        WITH total_drugs, count(n) as total_ndcs
        MATCH (b:Brand)
        WITH total_drugs, total_ndcs, count(b) as total_brands
        MATCH (s:Schedule)
        WITH total_drugs, total_ndcs, total_brands, count(s) as total_schedules
        RETURN 
            total_drugs,
            total_ndcs,
            total_brands,
            total_schedules
        """



"""
Neo4j Cypher queries for RxNorm Knowledge Graph with Gemini Embeddings.
Optimized queries using the actual schema from the imported data.
"""

# Health check for embedding-based schema
HEALTH_CHECK_QUERY = """
MATCH (d:Drug) WITH count(d) as total_drugs
MATCH (i:Ingredient) WITH total_drugs, count(i) as total_ingredients  
MATCH (b:Brand) WITH total_drugs, total_ingredients, count(b) as total_brands
MATCH (r:Route) WITH total_drugs, total_ingredients, total_brands, count(r) as total_routes
RETURN total_drugs as total_concepts, total_ingredients as total_attributes, 
       total_brands as total_sources, total_routes as total_semantic_types
"""

# Sample drug query
SAMPLE_DRUG_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS 'aspirin'
RETURN d.rxcui as concept_id, d.name as drug_name, d.strength, d.route
LIMIT 1
"""

# Primary drug search using actual schema properties
DRUG_SEARCH_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS toLower($drug_name) 
   OR toLower(d.full_name) CONTAINS toLower($drug_name)
   OR toLower(d.generic_name) CONTAINS toLower($drug_name)
   OR toLower(d.sxdg_name) CONTAINS toLower($drug_name)
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
OPTIONAL MATCH (d)-[:CONTAINS_INGREDIENT]->(i:Ingredient)
WITH d, b, collect(DISTINCT i.name) as ingredients,
     CASE 
        WHEN toLower(d.name) = toLower($drug_name) THEN 100
        WHEN toLower(d.name) STARTS WITH toLower($drug_name) THEN 95
        WHEN toLower(d.full_name) = toLower($drug_name) THEN 90
        WHEN toLower(d.generic_name) = toLower($drug_name) THEN 85
        WHEN toLower(d.sxdg_name) = toLower($drug_name) THEN 80
        WHEN toLower(d.name) CONTAINS toLower($drug_name) THEN 75
        ELSE 70
     END as match_score
RETURN 
    d.rxcui as concept_id,
    d.name as drug_name,
    d.full_name as concept_name,
    d.generic_name,
    d.sxdg_name as brand_name,
    d.strength,
    d.route,
    d.dose_form,
    d.term_type,
    d.psn,
    b.name as brand_drug,
    ingredients,
    match_score
ORDER BY match_score DESC, d.name ASC
LIMIT $limit
"""

# Exact drug match query
EXACT_DRUG_MATCH_QUERY = """
MATCH (d:Drug)
WHERE toLower(d.name) = toLower($drug_name) 
   OR toLower(d.full_name) = toLower($drug_name)
   OR toLower(d.generic_name) = toLower($drug_name)
   OR toLower(d.sxdg_name) = toLower($drug_name)
RETURN d.rxcui as concept_id, d.name as drug_name, d.strength, d.sxdg_name as brand_name
LIMIT 1
"""

# Comprehensive drug search with all relationships using actual schema
COMPREHENSIVE_DRUG_SEARCH = """
MATCH (d:Drug)
WHERE toLower(d.name) CONTAINS toLower($drug_name)
   OR toLower(d.full_name) CONTAINS toLower($drug_name)
   OR toLower(d.generic_name) CONTAINS toLower($drug_name)
   OR toLower(d.sxdg_name) CONTAINS toLower($drug_name)
   OR ($strength IS NOT NULL AND toLower(d.strength) CONTAINS toLower($strength))
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
OPTIONAL MATCH (d)-[:CONTAINS_INGREDIENT]->(i:Ingredient)
OPTIONAL MATCH (d)-[:HAS_INSTRUCTION]->(inst:Instruction)
OPTIONAL MATCH (d)-[:BELONGS_TO_CLASS]->(tc:TherapeuticClass)
WITH d, b, inst, tc,
     collect(DISTINCT i.name) as ingredients,
     CASE 
        WHEN toLower(d.name) = toLower($drug_name) THEN 100
        WHEN toLower(d.name) STARTS WITH toLower($drug_name) THEN 95
        WHEN toLower(d.full_name) = toLower($drug_name) THEN 90
        WHEN toLower(d.generic_name) = toLower($drug_name) THEN 85
        WHEN toLower(d.sxdg_name) = toLower($drug_name) THEN 80
        WHEN ($strength IS NOT NULL AND toLower(d.strength) CONTAINS toLower($strength)) THEN 75
        ELSE 70
     END as match_score
RETURN 
    d.rxcui as rxcui,
    d.name as drug_name,
    d.full_name as full_name,
    d.generic_name as generic_name,
    d.sxdg_name as brand_name,
    d.strength as strength,
    d.route as route,
    d.dose_form as dose_form,
    d.term_type as term_type,
    d.psn as psn,
    d.embedding as embedding,
    b.name as brand_drug,
    inst.template as instruction_template,
    tc.name as therapeutic_class,
    ingredients,
    match_score
ORDER BY match_score DESC, d.name ASC
LIMIT $limit
"""

# Drug details with full context using actual schema
DRUG_DETAILS_QUERY = """
MATCH (d:Drug {rxcui: $concept_id})
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
OPTIONAL MATCH (d)-[:CONTAINS_INGREDIENT]->(i:Ingredient)
OPTIONAL MATCH (d)-[:HAS_INSTRUCTION]->(inst:Instruction)
OPTIONAL MATCH (d)-[:BELONGS_TO_CLASS]->(tc:TherapeuticClass)
OPTIONAL MATCH (d)-[:GENERIC_VERSION]->(generic:Drug)
OPTIONAL MATCH (d)-[:BRANDED_VERSION]->(branded:Drug)
RETURN 
    d.rxcui as rxcui,
    d.name as drug_name,
    d.full_name as full_name,
    d.generic_name as generic_name,
    d.sxdg_name as brand_name,
    d.strength as strength,
    d.route as route,
    d.dose_form as dose_form,
    d.term_type as term_type,
    d.psn as psn,
    d.embedding as embedding,
    b.name as brand_drug,
    inst.template as instruction_template,
    tc.name as therapeutic_class,
    generic.name as generic_equivalent,
    branded.name as branded_equivalent,
    collect(DISTINCT {
        name: i.name,
        rxcui: i.ing_rxcui
    }) as ingredients
"""

# Semantic search using Gemini embeddings
EMBEDDING_SIMILARITY_SEARCH = """
MATCH (d:Drug)
WHERE d.embedding IS NOT NULL
WITH d,
     CASE 
        WHEN toLower(d.name) = toLower($drug_name) THEN 100
        WHEN toLower(d.name) CONTAINS toLower($drug_name) THEN 90
        WHEN toLower(d.full_name) CONTAINS toLower($drug_name) THEN 85
        WHEN toLower(d.generic_name) CONTAINS toLower($drug_name) THEN 80
        WHEN toLower(d.sxdg_name) CONTAINS toLower($drug_name) THEN 75
        ELSE 0
     END as text_score
WHERE text_score > 0
OPTIONAL MATCH (d)-[:CONTAINS_INGREDIENT]->(i:Ingredient)
OPTIONAL MATCH (d)-[:HAS_BRAND]->(b:Brand)
OPTIONAL MATCH (d)-[:HAS_INSTRUCTION]->(inst:Instruction)
RETURN 
    d.rxcui as rxcui,
    d.name as drug_name,
    d.full_name as full_name,
    d.generic_name as generic_name,
    d.sxdg_name as brand_name,
    d.strength as strength,
    d.route as route,
    d.dose_form as dose_form,
    d.embedding as embedding,
    b.name as brand_drug,
    inst.template as instruction,
    collect(DISTINCT i.name) as ingredients,
    text_score
ORDER BY text_score DESC, d.name ASC
LIMIT $limit
"""
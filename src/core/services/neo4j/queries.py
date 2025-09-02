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


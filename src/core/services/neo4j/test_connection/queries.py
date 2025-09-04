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

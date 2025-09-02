"""
Synonym Search Module
Handles synonym mapping from Excel sheet and searches in RxNorm
"""

from typing import Dict, Any, List
import pandas as pd
from pathlib import Path
from neo4j import AsyncGraphDatabase
from src.core.settings.config import settings
from src.core.settings.logging import logger
from .queries import (
    search_synonym_in_rxnorm,
    search_synonym_with_strength_in_rxnorm
)

class SynonymSearchService:
    """Service for synonym-based drug searching using Excel mapping"""
    
    def __init__(self, driver):
        self.driver = driver
        self.synonym_map = {}
        self._load_synonyms()
    
    def _load_synonyms(self):
        """Load synonyms from Synonyms.xlsx file"""
        try:
            synonym_file = Path("data/Synonyms.xlsx")
            if not synonym_file.exists():
                logger.warning("Synonyms.xlsx not found, synonym search will be limited")
                return
            
            df = pd.read_excel(synonym_file, engine='openpyxl')
            logger.info(f"Loading synonyms from: {synonym_file}")
            
            # Use first two columns as drug and synonym
            if len(df.columns) >= 2:
                drug_col = df.columns[0]
                synonym_col = df.columns[1]
                
                for _, row in df.iterrows():
                    drug = str(row[drug_col]).strip().lower() if pd.notna(row[drug_col]) else ""
                    synonym = str(row[synonym_col]).strip().lower() if pd.notna(row[synonym_col]) else ""
                    
                    if drug and synonym and drug != synonym:
                        # Bidirectional mapping
                        self.synonym_map[synonym] = {
                            "mapped_name": drug,
                            "original_synonym": str(row[synonym_col]).strip(),
                            "original_drug": str(row[drug_col]).strip()
                        }
                        self.synonym_map[drug] = {
                            "mapped_name": synonym,
                            "original_synonym": str(row[drug_col]).strip(),
                            "original_drug": str(row[synonym_col]).strip()
                        }
                
                logger.info(f"Loaded {len(self.synonym_map)} synonym mappings")
            
        except Exception as e:
            logger.error(f"Failed to load synonyms: {e}")
    
    def get_synonyms(self, drug_name: str) -> List[str]:
        """Get synonyms for a drug name"""
        drug_lower = drug_name.lower()
        synonyms = []
        
        # Direct mapping
        if drug_lower in self.synonym_map:
            synonyms.append(self.synonym_map[drug_lower]["mapped_name"])
        
        # Partial matching for similar names
        for mapped_name, mapping in self.synonym_map.items():
            if drug_lower in mapped_name or mapped_name in drug_lower:
                if mapping["mapped_name"] not in synonyms:
                    synonyms.append(mapping["mapped_name"])
        
        return synonyms
    
    async def search_by_synonyms(self, drug_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs using synonym mappings"""
        try:
            synonyms = self.get_synonyms(drug_name)
            if not synonyms:
                logger.info(f"No synonyms found for '{drug_name}'")
                return []
            
            all_results = []
            
            # Search for each synonym
            for synonym in synonyms:
                results = await self._search_synonym_in_rxnorm(synonym, limit)
                for result in results:
                    result["original_query"] = drug_name
                    result["synonym_used"] = synonym
                    result["search_method"] = "synonym_mapping"
                all_results.extend(results)
            
            # Remove duplicates based on rxcui
            seen_rxcuis = set()
            unique_results = []
            for result in all_results:
                rxcui = result.get("rxcui")
                if rxcui and rxcui not in seen_rxcuis:
                    seen_rxcuis.add(rxcui)
                    unique_results.append(result)
            
            logger.info(f"Synonym search found {len(unique_results)} unique results for '{drug_name}' using {len(synonyms)} synonyms")
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Synonym search failed: {e}")
            return []
    
    async def _search_synonym_in_rxnorm(self, synonym: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for a specific synonym in RxNorm"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_synonym_in_rxnorm 
                
                result = await session.run(query, synonym=synonym, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "match_confidence": float(record.get("match_confidence", 0.7))
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Synonym RxNorm search failed for '{synonym}': {e}")
            return []
    
    async def search_synonyms_with_strength(self, drug_name: str, strength: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for drugs using synonym mappings with strength consideration"""
        try:
            synonyms = self.get_synonyms(drug_name)
            if not synonyms:
                return []
            
            all_results = []
            
            # Search for each synonym with strength
            for synonym in synonyms:
                results = await self._search_synonym_with_strength_in_rxnorm(synonym, strength, limit)
                for result in results:
                    result["original_query"] = drug_name
                    result["synonym_used"] = synonym
                    result["search_method"] = "synonym_mapping_with_strength"
                all_results.extend(results)
            
            # Remove duplicates and sort by confidence
            seen_rxcuis = set()
            unique_results = []
            for result in all_results:
                rxcui = result.get("rxcui")
                if rxcui and rxcui not in seen_rxcuis:
                    seen_rxcuis.add(rxcui)
                    unique_results.append(result)
            
            # Sort by confidence
            unique_results.sort(key=lambda x: x.get("match_confidence", 0), reverse=True)
            
            logger.info(f"Synonym search with strength found {len(unique_results)} results for '{drug_name} {strength}'")
            return unique_results[:limit]
            
        except Exception as e:
            logger.error(f"Synonym search with strength failed: {e}")
            return []
    
    async def _search_synonym_with_strength_in_rxnorm(self, synonym: str, strength: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for a synonym with strength in RxNorm"""
        try:
            async with self.driver.session(database=settings.neo4j_database) as session:
                query = search_synonym_with_strength_in_rxnorm
                
                result = await session.run(query, synonym=synonym, strength=strength, limit=limit)
                
                drugs = []
                async for record in result:
                    drugs.append({
                        "rxcui": record.get("rxcui"),
                        "drug_name": record.get("drug_name"),
                        "full_name": record.get("full_name"),
                        "generic_name": record.get("generic_name"),
                        "strength": record.get("strength"),
                        "route": record.get("route"),
                        "dose_form": record.get("dose_form"),
                        "term_type": record.get("term_type"),
                        "match_confidence": float(record.get("match_confidence", 0.8))
                    })
                
                return drugs
                
        except Exception as e:
            logger.error(f"Synonym with strength search failed for '{synonym} {strength}': {e}")
            return []

"""
Synonym Search Module
Handles synonym mapping from Excel sheet and searches in RxNorm
"""

import pandas as pd
from pathlib import Path
from src.core.settings.logging import logger
from typing import List


class SynonymSearch:
    """Service for synonym-based drug searching using Excel mapping"""
    
    def __init__(self):
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
                print(drug_col, synonym_col)
                
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
        synonyms = set()

        # Debug: Log what's being searched
        logger.debug(f"Searching synonyms for '{drug_name}' (lowercase: '{drug_lower}')")

        # Direct mapping
        if drug_lower in self.synonym_map:
            synonyms.add(self.synonym_map[drug_lower]["mapped_name"])
            logger.debug(f"Found direct synonym mapping: {drug_lower} -> {self.synonym_map[drug_lower]['mapped_name']}")

        # Partial matching for similar names
        for mapped_name, mapping in self.synonym_map.items():
            if drug_lower in mapped_name or mapped_name in drug_lower:
                synonyms.add(mapping["mapped_name"])
                logger.debug(f"Found partial synonym mapping: {mapped_name} -> {mapping['mapped_name']}")

        if not synonyms:
            logger.debug(f"No synonyms found for '{drug_name}'. Available mappings sample: {list(self.synonym_map.keys())[:5]}")

        return list(synonyms)
   
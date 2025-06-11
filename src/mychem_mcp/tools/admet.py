# src/mychem_mcp/tools/admet.py
"""ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) tools."""

from typing import Any, Dict, Optional
import mcp.types as types
from ..client import MyChemClient


class ADMETApi:
    """Tools for ADMET properties."""
    
    async def get_admet_properties(
        self,
        client: MyChemClient,
        chemical_id: str
    ) -> Dict[str, Any]:
        """Get ADMET properties for a chemical."""
        params = {
            "fields": "chembl.absorption,chembl.distribution,chembl.metabolism,chembl.excretion,chembl.toxicity,drugbank.absorption,drugbank.metabolism,drugbank.toxicity,pubchem.molecular_weight,pubchem.logp,pubchem.tpsa"
        }
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        admet_data = {
            "chemical_id": chemical_id,
            "absorption": {},
            "distribution": {},
            "metabolism": {},
            "excretion": {},
            "toxicity": {},
            "physicochemical": {}
        }
        
        # Extract ChEMBL ADMET data
        if "chembl" in result:
            chembl = result["chembl"]
            if "absorption" in chembl:
                admet_data["absorption"]["chembl"] = chembl["absorption"]
            if "distribution" in chembl:
                admet_data["distribution"]["chembl"] = chembl["distribution"]
            if "metabolism" in chembl:
                admet_data["metabolism"]["chembl"] = chembl["metabolism"]
            if "excretion" in chembl:
                admet_data["excretion"]["chembl"] = chembl["excretion"]
            if "toxicity" in chembl:
                admet_data["toxicity"]["chembl"] = chembl["toxicity"]
        
        # Extract DrugBank ADMET data
        if "drugbank" in result:
            drugbank = result["drugbank"]
            if "absorption" in drugbank:
                admet_data["absorption"]["drugbank"] = drugbank["absorption"]
            if "metabolism" in drugbank:
                admet_data["metabolism"]["drugbank"] = drugbank["metabolism"]
            if "toxicity" in drugbank:
                admet_data["toxicity"]["drugbank"] = drugbank["toxicity"]
        
        # Extract physicochemical properties
        if "pubchem" in result:
            pubchem = result["pubchem"]
            if "molecular_weight" in pubchem:
                admet_data["physicochemical"]["molecular_weight"] = pubchem["molecular_weight"]
            if "logp" in pubchem:
                admet_data["physicochemical"]["logp"] = pubchem["logp"]
            if "tpsa" in pubchem:
                admet_data["physicochemical"]["tpsa"] = pubchem["tpsa"]
        
        return {
            "success": True,
            "admet_properties": admet_data
        }
    
    async def predict_toxicity(
        self,
        client: MyChemClient,
        chemical_id: str
    ) -> Dict[str, Any]:
        """Get toxicity predictions and data."""
        params = {
            "fields": "chembl.toxicity,drugbank.toxicity,pubchem.ld50,pharmgkb.toxicity,ghs.hazard_statements"
        }
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        toxicity_data = {
            "chemical_id": chemical_id,
            "acute_toxicity": {},
            "chronic_toxicity": {},
            "hazard_classification": {}
        }
        
        # Extract toxicity data from various sources
        if "chembl" in result and "toxicity" in result["chembl"]:
            toxicity_data["chembl_toxicity"] = result["chembl"]["toxicity"]
        
        if "drugbank" in result and "toxicity" in result["drugbank"]:
            toxicity_data["drugbank_toxicity"] = result["drugbank"]["toxicity"]
        
        if "pubchem" in result and "ld50" in result["pubchem"]:
            toxicity_data["acute_toxicity"]["ld50"] = result["pubchem"]["ld50"]
        
        if "ghs" in result and "hazard_statements" in result["ghs"]:
            toxicity_data["hazard_classification"]["ghs"] = result["ghs"]["hazard_statements"]
        
        return {
            "success": True,
            "toxicity_data": toxicity_data
        }


ADMET_TOOLS = [
    types.Tool(
        name="get_admet_properties",
        description="Get ADMET (Absorption, Distribution, Metabolism, Excretion, Toxicity) properties",
        inputSchema={
            "type": "object",
            "properties": {
                "chemical_id": {
                    "type": "string",
                    "description": "Chemical identifier"
                }
            },
            "required": ["chemical_id"]
        }
    ),
    types.Tool(
        name="predict_toxicity",
        description="Get toxicity predictions and hazard classifications",
        inputSchema={
            "type": "object",
            "properties": {
                "chemical_id": {
                    "type": "string",
                    "description": "Chemical identifier"
                }
            },
            "required": ["chemical_id"]
        }
    )
]
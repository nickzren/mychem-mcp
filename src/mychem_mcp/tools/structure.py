# src/mychem_mcp/tools/structure.py
"""Chemical structure tools."""

from typing import Any, Dict, Optional
import mcp.types as types
from ..client import MyChemClient


class StructureApi:
    """Tools for chemical structure operations."""
    
    async def get_chemical_structure(
        self,
        client: MyChemClient,
        chemical_id: str,
        format: str = "all"
    ) -> Dict[str, Any]:
        """Get chemical structure representations."""
        fields_map = {
            "smiles": "pubchem.smiles.canonical,chembl.smiles,drugbank.smiles",
            "inchi": "pubchem.inchi,chembl.inchi,drugbank.inchi",
            "inchikey": "pubchem.inchikey,chembl.inchikey,drugbank.inchikey",
            "mol": "pubchem.sdf,chembl.molecule_structures",
            "all": "pubchem.smiles,pubchem.inchi,pubchem.inchikey,chembl.smiles,chembl.inchi,chembl.inchikey,drugbank.smiles,drugbank.inchi,drugbank.inchikey"
        }
        
        params = {"fields": fields_map.get(format, fields_map["all"])}
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        return {
            "success": True,
            "chemical_id": chemical_id,
            "structures": result
        }
    
    async def search_by_structure(
        self,
        client: MyChemClient,
        structure: str,
        structure_type: str = "smiles",
        similarity: Optional[float] = 0.8,
        size: Optional[int] = 10
    ) -> Dict[str, Any]:
        """Search for similar chemicals by structure."""
        query_map = {
            "smiles": f"pubchem.smiles.canonical:{structure} OR chembl.smiles:{structure}",
            "inchi": f"pubchem.inchi:{structure} OR chembl.inchi:{structure}",
            "inchikey": f"pubchem.inchikey:{structure} OR chembl.inchikey:{structure}"
        }
        
        params = {
            "q": query_map.get(structure_type, f"pubchem.smiles.canonical:{structure}"),
            "size": size
        }
        
        result = await client.get("query", params=params)
        
        return {
            "success": True,
            "query_structure": structure,
            "structure_type": structure_type,
            "total": result.get("total", 0),
            "hits": result.get("hits", [])
        }
    
    async def convert_structure(
        self,
        client: MyChemClient,
        structure: str,
        from_format: str,
        to_format: str
    ) -> Dict[str, Any]:
        """Convert between structure formats by finding the chemical first."""
        # First find the chemical
        search_result = await self.search_by_structure(
            client, structure, from_format, size=1
        )
        
        if search_result["total"] == 0:
            return {
                "success": False,
                "error": "Chemical not found with the provided structure"
            }
        
        # Get the chemical ID
        chemical_id = search_result["hits"][0].get("_id")
        
        # Get the desired format
        structure_result = await self.get_chemical_structure(
            client, chemical_id, to_format
        )
        
        return {
            "success": True,
            "input_structure": structure,
            "from_format": from_format,
            "to_format": to_format,
            "converted_structure": structure_result["structures"]
        }


STRUCTURE_TOOLS = [
    types.Tool(
        name="get_chemical_structure",
        description="Get chemical structure representations (SMILES, InChI, InChIKey)",
        inputSchema={
            "type": "object",
            "properties": {
                "chemical_id": {
                    "type": "string",
                    "description": "Chemical identifier"
                },
                "format": {
                    "type": "string",
                    "enum": ["smiles", "inchi", "inchikey", "mol", "all"],
                    "default": "all",
                    "description": "Structure format to retrieve"
                }
            },
            "required": ["chemical_id"]
        }
    ),
    types.Tool(
        name="search_by_structure",
        description="Search for similar chemicals by structure",
        inputSchema={
            "type": "object",
            "properties": {
                "structure": {
                    "type": "string",
                    "description": "Chemical structure string"
                },
                "structure_type": {
                    "type": "string",
                    "enum": ["smiles", "inchi", "inchikey"],
                    "default": "smiles",
                    "description": "Type of structure input"
                },
                "similarity": {
                    "type": "number",
                    "description": "Similarity threshold (0-1)",
                    "default": 0.8
                },
                "size": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 10
                }
            },
            "required": ["structure"]
        }
    ),
    types.Tool(
        name="convert_structure",
        description="Convert between chemical structure formats",
        inputSchema={
            "type": "object",
            "properties": {
                "structure": {
                    "type": "string",
                    "description": "Input structure"
                },
                "from_format": {
                    "type": "string",
                    "enum": ["smiles", "inchi", "inchikey"],
                    "description": "Input format"
                },
                "to_format": {
                    "type": "string",
                    "enum": ["smiles", "inchi", "inchikey"],
                    "description": "Output format"
                }
            },
            "required": ["structure", "from_format", "to_format"]
        }
    )
]
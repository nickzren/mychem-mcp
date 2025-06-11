# src/mychem_mcp/tools/structure.py
"""Enhanced chemical structure tools."""

from typing import Any, Dict, Optional, List
import mcp.types as types
from ..client import MyChemClient


class StructureApi:
    """Enhanced tools for chemical structure operations."""
    
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
    
    async def search_by_substructure(
        self,
        client: MyChemClient,
        substructure_smiles: str,
        additional_filters: Optional[Dict[str, Any]] = None,
        size: int = 100
    ) -> Dict[str, Any]:
        """Search for chemicals containing a specific substructure.
        
        Note: This is a simplified implementation. True substructure search
        would require server-side SMARTS pattern matching.
        """
        # For now, we'll search for chemicals and note that full substructure
        # search would need server-side support
        query_parts = [f'pubchem.smiles:*{substructure_smiles}*']
        
        # Add additional filters if provided
        if additional_filters:
            for field, value in additional_filters.items():
                query_parts.append(f"{field}:{value}")
        
        q = " AND ".join(query_parts)
        
        params = {
            "q": q,
            "fields": "inchikey,pubchem.smiles.canonical,chembl.smiles,name",
            "size": size
        }
        
        result = await client.get("query", params=params)
        
        return {
            "success": True,
            "substructure_query": substructure_smiles,
            "note": "This is a text-based search. True substructure search requires SMARTS pattern matching.",
            "total": result.get("total", 0),
            "hits": result.get("hits", [])
        }
    
    async def get_structure_properties(
        self,
        client: MyChemClient,
        chemical_id: str
    ) -> Dict[str, Any]:
        """Get detailed structural properties of a chemical."""
        fields = [
            "pubchem.molecular_formula",
            "pubchem.molecular_weight",
            "pubchem.monoisotopic_weight",
            "pubchem.canonical_smiles",
            "pubchem.isomeric_smiles",
            "pubchem.inchi",
            "pubchem.inchikey",
            "pubchem.iupac_name",
            "pubchem.xlogp",
            "pubchem.exact_mass",
            "pubchem.tpsa",
            "pubchem.complexity",
            "pubchem.h_bond_acceptor_count",
            "pubchem.h_bond_donor_count",
            "pubchem.rotatable_bond_count",
            "pubchem.heavy_atom_count",
            "pubchem.isotope_atom_count",
            "pubchem.atom_stereo_count",
            "pubchem.defined_atom_stereo_count",
            "pubchem.undefined_atom_stereo_count",
            "pubchem.bond_stereo_count",
            "pubchem.covalent_unit_count",
            "chembl.mw_freebase",
            "chembl.mw_monoisotopic",
            "chembl.alogp",
            "chembl.hba",
            "chembl.hbd",
            "chembl.psa",
            "chembl.rtb",
            "chembl.ro3_pass",
            "chembl.num_ro5_violations",
            "chembl.aromatic_rings",
            "chembl.heavy_atoms",
            "chembl.qed_weighted",
            "chembl.full_mwt"
        ]
        
        params = {"fields": ",".join(fields)}
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        # Organize properties by category
        properties = {
            "chemical_id": chemical_id,
            "basic_properties": {},
            "physicochemical_properties": {},
            "structural_features": {},
            "drug_like_properties": {}
        }
        
        # Extract PubChem properties
        if "pubchem" in result:
            pc = result["pubchem"]
            properties["basic_properties"].update({
                "molecular_formula": pc.get("molecular_formula"),
                "molecular_weight": pc.get("molecular_weight"),
                "monoisotopic_weight": pc.get("monoisotopic_weight"),
                "exact_mass": pc.get("exact_mass"),
                "iupac_name": pc.get("iupac_name")
            })
            
            properties["physicochemical_properties"].update({
                "xlogp": pc.get("xlogp"),
                "tpsa": pc.get("tpsa"),
                "complexity": pc.get("complexity")
            })
            
            properties["structural_features"].update({
                "h_bond_acceptor_count": pc.get("h_bond_acceptor_count"),
                "h_bond_donor_count": pc.get("h_bond_donor_count"),
                "rotatable_bond_count": pc.get("rotatable_bond_count"),
                "heavy_atom_count": pc.get("heavy_atom_count"),
                "atom_stereo_count": pc.get("atom_stereo_count"),
                "bond_stereo_count": pc.get("bond_stereo_count")
            })
        
        # Extract ChEMBL properties
        if "chembl" in result:
            chembl = result["chembl"]
            properties["drug_like_properties"].update({
                "ro3_pass": chembl.get("ro3_pass"),
                "num_ro5_violations": chembl.get("num_ro5_violations"),
                "qed_weighted": chembl.get("qed_weighted"),
                "aromatic_rings": chembl.get("aromatic_rings")
            })
        
        return {
            "success": True,
            "structure_properties": properties
        }
    
    async def calculate_similarity_matrix(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        similarity_metric: str = "tanimoto"
    ) -> Dict[str, Any]:
        """Calculate pairwise similarity between chemicals.
        
        Note: This would ideally use fingerprint-based similarity calculations.
        For now, we'll return structure data that could be used for similarity.
        """
        structures = {}
        
        # Fetch SMILES for all chemicals
        for chem_id in chemical_ids:
            try:
                result = await client.get(
                    f"chem/{chem_id}",
                    params={"fields": "pubchem.smiles.canonical,chembl.smiles,drugbank.name,chembl.pref_name"}
                )
                
                smiles = (result.get("pubchem", {}).get("smiles", {}).get("canonical") or
                         result.get("chembl", {}).get("smiles"))
                
                name = (result.get("drugbank", {}).get("name") or
                       result.get("chembl", {}).get("pref_name") or
                       chem_id)
                
                if smiles:
                    structures[chem_id] = {
                        "smiles": smiles,
                        "name": name
                    }
            except:
                pass
        
        return {
            "success": True,
            "note": "Full similarity calculation requires fingerprint computation. Structure data provided for external processing.",
            "similarity_metric": similarity_metric,
            "chemicals": structures,
            "matrix_size": f"{len(structures)}x{len(structures)}"
        }
    
    async def get_stereoisomers(
        self,
        client: MyChemClient,
        chemical_id: str
    ) -> Dict[str, Any]:
        """Get stereoisomer information for a chemical."""
        fields = [
            "pubchem.canonical_smiles",
            "pubchem.isomeric_smiles",
            "pubchem.cid",
            "chembl.chirality",
            "pubchem.atom_stereo_count",
            "pubchem.defined_atom_stereo_count",
            "pubchem.undefined_atom_stereo_count"
        ]
        
        params = {"fields": ",".join(fields)}
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        stereoisomer_info = {
            "chemical_id": chemical_id,
            "stereochemistry": {}
        }
        
        if "pubchem" in result:
            pc = result["pubchem"]
            stereoisomer_info["stereochemistry"] = {
                "canonical_smiles": pc.get("canonical_smiles"),
                "isomeric_smiles": pc.get("isomeric_smiles"),
                "total_stereocenters": pc.get("atom_stereo_count", 0),
                "defined_stereocenters": pc.get("defined_atom_stereo_count", 0),
                "undefined_stereocenters": pc.get("undefined_atom_stereo_count", 0)
            }
        
        if "chembl" in result:
            stereoisomer_info["stereochemistry"]["chirality"] = result["chembl"].get("chirality")
        
        # Search for related stereoisomers
        if stereoisomer_info["stereochemistry"].get("canonical_smiles"):
            canonical = stereoisomer_info["stereochemistry"]["canonical_smiles"]
            
            # Search for chemicals with same canonical SMILES
            search_params = {
                "q": f'pubchem.canonical_smiles:"{canonical}"',
                "fields": "pubchem.isomeric_smiles,pubchem.cid,name",
                "size": 10
            }
            
            related = await client.get("query", params=search_params)
            
            stereoisomer_info["related_isomers"] = []
            for hit in related.get("hits", []):
                if hit.get("_id") != chemical_id:  # Exclude self
                    stereoisomer_info["related_isomers"].append({
                        "inchikey": hit.get("_id"),
                        "name": hit.get("name"),
                        "isomeric_smiles": hit.get("pubchem", {}).get("isomeric_smiles"),
                        "cid": hit.get("pubchem", {}).get("cid")
                    })
        
        return {
            "success": True,
            "stereoisomer_data": stereoisomer_info
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
    ),
    types.Tool(
        name="search_by_substructure",
        description="Search for chemicals containing a specific substructure (simplified)",
        inputSchema={
            "type": "object",
            "properties": {
                "substructure_smiles": {
                    "type": "string",
                    "description": "SMILES of substructure to search for"
                },
                "additional_filters": {
                    "type": "object",
                    "description": "Additional field filters"
                },
                "size": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 100
                }
            },
            "required": ["substructure_smiles"]
        }
    ),
    types.Tool(
        name="get_structure_properties",
        description="Get detailed structural and physicochemical properties",
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
        name="calculate_similarity_matrix",
        description="Get structure data for pairwise similarity calculation",
        inputSchema={
            "type": "object",
            "properties": {
                "chemical_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chemical identifiers"
                },
                "similarity_metric": {
                    "type": "string",
                    "description": "Similarity metric to use",
                    "default": "tanimoto",
                    "enum": ["tanimoto", "dice", "cosine"]
                }
            },
            "required": ["chemical_ids"]
        }
    ),
    types.Tool(
        name="get_stereoisomers",
        description="Get stereoisomer information and related isomers",
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
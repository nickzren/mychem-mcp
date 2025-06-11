# src/mychem_mcp/tools/mapping.py
"""Chemical identifier mapping tools."""

from typing import Any, Dict, List, Optional
import mcp.types as types
from ..client import MyChemClient, MyChemError


class MappingApi:
    """Tools for mapping between chemical identifiers."""
    
    async def map_identifiers(
        self,
        client: MyChemClient,
        input_ids: List[str],
        from_type: str,
        to_types: List[str],
        missing_ok: bool = True
    ) -> Dict[str, Any]:
        """Map chemical identifiers from one type to multiple other types.
        
        Supported identifier types:
        - inchikey: InChIKey
        - pubchem: PubChem CID
        - chembl: ChEMBL ID
        - drugbank: DrugBank ID
        - unii: FDA UNII
        - cas: CAS Registry Number
        - smiles: SMILES string
        - inchi: InChI string
        - name: Chemical name
        """
        # Define field mappings
        field_map = {
            "inchikey": "pubchem.inchikey,chembl.inchikey,drugbank.inchikey",
            "pubchem": "pubchem.cid",
            "chembl": "chembl.molecule_chembl_id",
            "drugbank": "drugbank.id",
            "unii": "unii.unii",
            "cas": "drugbank.cas_number,pubchem.cas",
            "smiles": "pubchem.smiles.canonical,chembl.smiles",
            "inchi": "pubchem.inchi,chembl.inchi",
            "name": "chembl.pref_name,drugbank.name,pubchem.synonyms"
        }
        
        # Build scope for searching
        scope = field_map.get(from_type)
        if not scope:
            raise MyChemError(f"Unsupported from_type: {from_type}")
        
        # Build fields to return
        return_fields = ["_id"]  # Always include InChIKey
        for to_type in to_types:
            if to_type in field_map:
                return_fields.append(field_map[to_type])
        
        # Query for all identifiers
        post_data = {
            "ids": input_ids,
            "scopes": scope,
            "fields": ",".join(return_fields)
        }
        
        results = await client.post("query", post_data)
        
        # Process results
        mappings = []
        unmapped = []
        
        for result in results:
            if result.get("found", False):
                mapping = {
                    "input": result.get("query"),
                    "from_type": from_type,
                    "mappings": {}
                }
                
                # Extract each requested identifier type
                for to_type in to_types:
                    value = None
                    
                    if to_type == "inchikey":
                        value = result.get("_id")
                    elif to_type == "pubchem":
                        value = result.get("pubchem", {}).get("cid")
                    elif to_type == "chembl":
                        value = result.get("chembl", {}).get("molecule_chembl_id")
                    elif to_type == "drugbank":
                        value = result.get("drugbank", {}).get("id")
                    elif to_type == "unii":
                        value = result.get("unii", {}).get("unii")
                    elif to_type == "cas":
                        value = (result.get("drugbank", {}).get("cas_number") or
                                result.get("pubchem", {}).get("cas"))
                    elif to_type == "smiles":
                        value = (result.get("pubchem", {}).get("smiles", {}).get("canonical") or
                                result.get("chembl", {}).get("smiles"))
                    elif to_type == "inchi":
                        value = (result.get("pubchem", {}).get("inchi") or
                                result.get("chembl", {}).get("inchi"))
                    elif to_type == "name":
                        value = (result.get("chembl", {}).get("pref_name") or
                                result.get("drugbank", {}).get("name") or
                                (result.get("pubchem", {}).get("synonyms", [None])[0] if isinstance(result.get("pubchem", {}).get("synonyms"), list) else None))
                    
                    if value:
                        mapping["mappings"][to_type] = value
                
                mappings.append(mapping)
            else:
                unmapped.append(result.get("query", "Unknown"))
        
        return {
            "success": True,
            "total_input": len(input_ids),
            "mapped": len(mappings),
            "unmapped": len(unmapped),
            "mappings": mappings,
            "unmapped_ids": unmapped
        }
    
    async def validate_identifiers(
    self,
    client: MyChemClient,
    identifiers: List[str],
    identifier_type: str
    ) -> Dict[str, Any]:
        """Validate a list of chemical identifiers."""
        # Use mapping to check validity
        result = await self.map_identifiers(
            client=client,
            input_ids=identifiers,
            from_type=identifier_type,
            to_types=["inchikey"],  # Just need to check if found
            missing_ok=True
        )
        
        valid = []
        invalid = []
        
        for mapping in result["mappings"]:
            valid.append({
                "identifier": mapping["input"],
                "inchikey": mapping["mappings"].get("inchikey")
            })
        
        # Get invalid from unmapped_ids
        invalid = result.get("unmapped_ids", [])
        
        return {
            "success": True,
            "identifier_type": identifier_type,
            "total": len(identifiers),
            "valid_count": len(valid),
            "invalid_count": len(invalid),
            "valid_identifiers": valid,
            "invalid_identifiers": invalid
        }
    
    async def find_common_identifiers(
        self,
        client: MyChemClient,
        identifier_lists: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Find chemicals common across multiple identifier lists.
        
        Example input:
        {
            "drugbank_ids": ["DB00945", "DB00316"],
            "chembl_ids": ["CHEMBL25", "CHEMBL116"]
        }
        """
        all_inchikeys = {}
        
        # Map all identifiers to InChIKeys
        for id_type, id_list in identifier_lists.items():
            # Determine the identifier type
            if "drugbank" in id_type.lower():
                from_type = "drugbank"
            elif "chembl" in id_type.lower():
                from_type = "chembl"
            elif "pubchem" in id_type.lower() or "cid" in id_type.lower():
                from_type = "pubchem"
            elif "cas" in id_type.lower():
                from_type = "cas"
            else:
                raise ValueError(f"Cannot determine identifier type from: {id_type}")
            
            mapping_result = await self.map_identifiers(
                client=client,
                input_ids=id_list,
                from_type=from_type,
                to_types=["inchikey", "name"]
            )
            
            for mapping in mapping_result["mappings"]:
                inchikey = mapping["mappings"].get("inchikey")
                if inchikey:
                    if inchikey not in all_inchikeys:
                        all_inchikeys[inchikey] = {
                            "name": mapping["mappings"].get("name"),
                            "found_in": []
                        }
                    all_inchikeys[inchikey]["found_in"].append({
                        "list": id_type,
                        "identifier": mapping["input"]
                    })
        
        # Find common chemicals
        common_chemicals = []
        list_names = list(identifier_lists.keys())
        
        for inchikey, data in all_inchikeys.items():
            found_lists = [item["list"] for item in data["found_in"]]
            if all(list_name in found_lists for list_name in list_names):
                common_chemicals.append({
                    "inchikey": inchikey,
                    "name": data["name"],
                    "identifiers": data["found_in"]
                })
        
        return {
            "success": True,
            "input_lists": list_names,
            "total_unique_chemicals": len(all_inchikeys),
            "common_chemicals_count": len(common_chemicals),
            "common_chemicals": common_chemicals
        }


MAPPING_TOOLS = [
    types.Tool(
        name="map_identifiers",
        description="Map chemical identifiers from one type to others (InChIKey, PubChem CID, ChEMBL ID, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "input_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of input identifiers"
                },
                "from_type": {
                    "type": "string",
                    "enum": ["inchikey", "pubchem", "chembl", "drugbank", "unii", "cas", "smiles", "inchi", "name"],
                    "description": "Type of input identifiers"
                },
                "to_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["inchikey", "pubchem", "chembl", "drugbank", "unii", "cas", "smiles", "inchi", "name"]
                    },
                    "description": "Types to map to"
                },
                "missing_ok": {
                    "type": "boolean",
                    "description": "Whether to include unmapped IDs in response",
                    "default": True
                }
            },
            "required": ["input_ids", "from_type", "to_types"]
        }
    ),
    types.Tool(
        name="validate_identifiers",
        description="Validate a list of chemical identifiers",
        inputSchema={
            "type": "object",
            "properties": {
                "identifiers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of identifiers to validate"
                },
                "identifier_type": {
                    "type": "string",
                    "enum": ["inchikey", "pubchem", "chembl", "drugbank", "unii", "cas", "smiles", "inchi"],
                    "description": "Type of identifiers"
                }
            },
            "required": ["identifiers", "identifier_type"]
        }
    ),
    types.Tool(
        name="find_common_identifiers",
        description="Find chemicals common across multiple identifier lists",
        inputSchema={
            "type": "object",
            "properties": {
                "identifier_lists": {
                    "type": "object",
                    "description": "Named lists of identifiers (e.g., {'drugbank_ids': [...], 'chembl_ids': [...]})"
                }
            },
            "required": ["identifier_lists"]
        }
    )
]
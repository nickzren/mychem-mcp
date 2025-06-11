# src/mychem_mcp/tools/export.py
"""Data export tools."""

from typing import Any, Dict, List, Optional
import json
import csv
import io
import mcp.types as types
from ..client import MyChemClient


class ExportApi:
    """Tools for exporting chemical data."""
    
    async def export_chemical_list(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        format: str = "tsv",
        fields: Optional[List[str]] = None
    ) -> str:
        """Export chemical data in various formats."""
        # Default fields if not specified
        if not fields:
            fields = ["inchikey", "name", "pubchem.cid", "chembl.molecule_chembl_id", "drugbank.id", "molecular_formula"]
        
        # Fetch chemical data
        fields_str = ",".join(fields)
        post_data = {
            "ids": chemical_ids,
            "fields": fields_str
        }
        
        results = await client.post("chem", post_data)
        
        # Format based on requested type
        if format == "json":
            return json.dumps(results, indent=2)
        
        elif format in ["tsv", "csv"]:
            # Flatten nested fields
            flattened_results = []
            for chem in results:
                flat_chem = {}
                for field in fields:
                    if "." in field:
                        # Handle nested fields
                        parts = field.split(".")
                        value = chem
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = None
                                break
                        flat_chem[field] = value
                    else:
                        flat_chem[field] = chem.get(field)
                
                flattened_results.append(flat_chem)
            
            # Create CSV/TSV
            output = io.StringIO()
            delimiter = "\t" if format == "tsv" else ","
            writer = csv.DictWriter(output, fieldnames=fields, delimiter=delimiter)
            
            writer.writeheader()
            writer.writerows(flattened_results)
            
            return output.getvalue()
        
        elif format == "sdf":
            # Simple SDF format (would need proper SDF library for complete implementation)
            sdf_output = []
            for chem in results:
                sdf_output.append(f"> <INCHIKEY>")
                sdf_output.append(chem.get("inchikey", ""))
                sdf_output.append("")
                sdf_output.append(f"> <NAME>")
                sdf_output.append(chem.get("name", ""))
                sdf_output.append("")
                sdf_output.append("$$$$")
            
            return "\n".join(sdf_output)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


EXPORT_TOOLS = [
    types.Tool(
        name="export_chemical_list",
        description="Export chemical data in various formats (TSV, CSV, JSON, SDF)",
        inputSchema={
            "type": "object",
            "properties": {
                "chemical_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of chemical IDs to export"
                },
                "format": {
                    "type": "string",
                    "description": "Export format",
                    "default": "tsv",
                    "enum": ["tsv", "csv", "json", "sdf"]
                },
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Fields to include in export"
                }
            },
            "required": ["chemical_ids"]
        }
    )
]
# src/mychem_mcp/tools/annotation.py
"""Chemical annotation tools."""

from typing import Any, Dict, Optional
from ..client import MyChemClient


class AnnotationApi:
    """Tools for retrieving chemical annotations."""
    
    async def get_chemical_by_id(
        self,
        client: MyChemClient,
        chemical_id: str,
        fields: Optional[str] = None,
        dotfield: Optional[bool] = True
    ) -> Dict[str, Any]:
        """Get detailed information about a chemical by ID."""
        params = {}
        if fields:
            params["fields"] = fields
        if not dotfield:
            params["dotfield"] = "false"
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        return {
            "success": True,
            "chemical": result
        }

# src/mychem_mcp/tools/batch.py
"""Batch operation tools."""

from typing import Any, Dict, List, Optional

from ..client import MyChemClient, MyChemError

MAX_BATCH_SIZE = 1000


class BatchApi:
    """Tools for batch operations on chemicals."""

    @staticmethod
    def _normalize_results(results: Any) -> List[Dict[str, Any]]:
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        if isinstance(results, dict):
            return [results]
        raise MyChemError("Unexpected response format from MyChem API")
    
    async def batch_query_chemicals(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        scopes: Optional[str] = "inchikey,chembl.molecule_chembl_id,drugbank.id,pubchem.cid",
        fields: Optional[str] = "inchikey,pubchem,chembl,drugbank,name",
        dotfield: Optional[bool] = True,
        returnall: Optional[bool] = True
    ) -> Dict[str, Any]:
        """Query multiple chemicals in a single request."""
        if len(chemical_ids) > MAX_BATCH_SIZE:
            raise MyChemError(f"Batch size exceeds maximum of {MAX_BATCH_SIZE}")
        
        post_data = {
            "ids": chemical_ids,
            "scopes": scopes,
            "fields": fields
        }
        if not dotfield:
            post_data["dotfield"] = False
        if returnall is not None:
            post_data["returnall"] = returnall
        
        raw_results = await client.post("query", post_data)
        results = self._normalize_results(raw_results)
        
        # Process results
        found = []
        missing = []
        for result in results:
            if result.get("found", False):
                found.append(result)
            else:
                missing.append(result.get("query", "Unknown"))
        
        return {
            "success": True,
            "total": len(results),
            "found": len(found),
            "missing": len(missing),
            "results": results,
            "missing_ids": missing
        }
    
    async def batch_get_chemicals(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        fields: Optional[str] = None,
        dotfield: Optional[bool] = True,
        email: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get annotations for multiple chemicals in a single request."""
        if len(chemical_ids) > MAX_BATCH_SIZE:
            raise MyChemError(f"Batch size exceeds maximum of {MAX_BATCH_SIZE}")
        
        post_data = {"ids": chemical_ids}
        if fields:
            post_data["fields"] = fields
        if not dotfield:
            post_data["dotfield"] = False
        if email:
            post_data["email"] = email
        
        results = await client.post("chem", post_data)
        normalized_results = self._normalize_results(results)
        
        return {
            "success": True,
            "total": len(normalized_results),
            "chemicals": normalized_results
        }

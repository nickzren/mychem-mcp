# src/mychem_mcp/tools/query.py
"""Chemical query tools."""

from typing import Any, Dict, Optional
import mcp.types as types
from ..client import MyChemClient


class QueryApi:
    """Tools for querying chemicals."""
    
    async def search_chemical(
        self,
        client: MyChemClient,
        q: str,
        fields: Optional[str] = "inchikey,pubchem,chembl,drugbank,name",
        size: Optional[int] = 10,
        from_: Optional[int] = None,
        sort: Optional[str] = None,
        facets: Optional[str] = None,
        facet_size: Optional[int] = 10,
        fetch_all: Optional[bool] = False,
        scroll_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search for chemicals using various query types."""
        params = {"q": q}
        if fields:
            params["fields"] = fields
        if size is not None:
            params["size"] = size
        if from_ is not None:
            params["from"] = from_
        if sort:
            params["sort"] = sort
        if facets:
            params["facets"] = facets
            params["facet_size"] = facet_size
        if fetch_all:
            params["fetch_all"] = "true"
        if scroll_id:
            params["scroll_id"] = scroll_id
        
        result = await client.get("query", params=params)
        
        return {
            "success": True,
            "total": result.get("total", 0),
            "took": result.get("took", 0),
            "hits": result.get("hits", []),
            "scroll_id": result.get("_scroll_id"),
            "facets": result.get("facets", {})
        }
    
    async def search_by_field(
        self,
        client: MyChemClient,
        field_queries: Dict[str, str],
        operator: str = "AND",
        fields: Optional[str] = "inchikey,pubchem,chembl,drugbank,name",
        size: Optional[int] = 10
    ) -> Dict[str, Any]:
        """Search by specific fields with boolean operators."""
        query_parts = []
        for field, value in field_queries.items():
            if " " in value and not (value.startswith('"') and value.endswith('"')):
                value = f'"{value}"'
            query_parts.append(f"{field}:{value}")
        
        q = f" {operator} ".join(query_parts)
        
        return await self.search_chemical(
            client=client,
            q=q,
            fields=fields,
            size=size
        )
    
    async def get_field_statistics(
        self,
        client: MyChemClient,
        field: str,
        size: int = 100
    ) -> Dict[str, Any]:
        """Get statistics for a specific field."""
        params = {
            "q": "*",
            "facets": field,
            "facet_size": size,
            "size": 0
        }
        
        result = await client.get("query", params=params)
        
        facet_data = result.get("facets", {}).get(field, {})
        terms = facet_data.get("terms", [])
        
        return {
            "success": True,
            "field": field,
            "total_unique_values": facet_data.get("total", 0),
            "top_values": [
                {
                    "value": term["term"],
                    "count": term["count"],
                    "percentage": round(term["count"] / result.get("total", 1) * 100, 2)
                }
                for term in terms
            ],
            "total_chemicals": result.get("total", 0)
        }


QUERY_TOOLS = [
    types.Tool(
        name="search_chemical",
        description="Search for chemicals using various query types (name, formula, InChI, SMILES, etc.)",
        inputSchema={
            "type": "object",
            "properties": {
                "q": {
                    "type": "string",
                    "description": "Query string (e.g., 'aspirin', 'C9H8O4', 'BSYNRYMUTXBXSQ-UHFFFAOYSA-N')"
                },
                "fields": {
                    "type": "string",
                    "description": "Comma-separated fields to return",
                    "default": "inchikey,pubchem,chembl,drugbank,name"
                },
                "size": {
                    "type": "integer",
                    "description": "Number of results to return (max 1000)",
                    "default": 10
                },
                "from_": {
                    "type": "integer",
                    "description": "Starting result offset for pagination"
                },
                "sort": {
                    "type": "string",
                    "description": "Sort order for results"
                },
                "facets": {
                    "type": "string",
                    "description": "Facet fields for aggregation"
                },
                "facet_size": {
                    "type": "integer",
                    "description": "Number of facet results",
                    "default": 10
                },
                "fetch_all": {
                    "type": "boolean",
                    "description": "Fetch all results (returns scroll_id)",
                    "default": False
                },
                "scroll_id": {
                    "type": "string",
                    "description": "Scroll ID for fetching next batch"
                }
            },
            "required": ["q"]
        }
    ),
    types.Tool(
        name="search_by_field",
        description="Search chemicals by specific field values with boolean logic",
        inputSchema={
            "type": "object",
            "properties": {
                "field_queries": {
                    "type": "object",
                    "description": "Field-value pairs (e.g., {'chembl.molecule_chembl_id': 'CHEMBL25'})"
                },
                "operator": {
                    "type": "string",
                    "description": "Boolean operator: AND or OR",
                    "default": "AND",
                    "enum": ["AND", "OR"]
                },
                "fields": {
                    "type": "string",
                    "description": "Fields to return",
                    "default": "inchikey,pubchem,chembl,drugbank,name"
                },
                "size": {
                    "type": "integer",
                    "description": "Number of results",
                    "default": 10
                }
            },
            "required": ["field_queries"]
        }
    ),
    types.Tool(
        name="get_field_statistics",
        description="Get statistics and top values for a specific field",
        inputSchema={
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": "Field to analyze (e.g., 'chembl.molecule_type', 'drugbank.groups')"
                },
                "size": {
                    "type": "integer",
                    "description": "Number of top values to return",
                    "default": 100
                }
            },
            "required": ["field"]
        }
    )
]
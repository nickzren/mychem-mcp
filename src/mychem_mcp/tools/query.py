# src/mychem_mcp/tools/query.py
"""Enhanced chemical query tools."""

from typing import Any, Dict, Optional, List
from ..client import MyChemClient


class QueryApi:
    """Enhanced tools for querying chemicals."""
    
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
        total_chemicals = result.get("total", 0)
        percentage_base = total_chemicals if total_chemicals > 0 else 1
        
        return {
            "success": True,
            "field": field,
            "total_unique_values": facet_data.get("total", 0),
            "top_values": [
                {
                    "value": term["term"],
                    "count": term["count"],
                    "percentage": round(term["count"] / percentage_base * 100, 2)
                }
                for term in terms
            ],
            "total_chemicals": total_chemicals
        }
    
    async def search_by_molecular_properties(
        self,
        client: MyChemClient,
        mw_min: Optional[float] = None,
        mw_max: Optional[float] = None,
        logp_min: Optional[float] = None,
        logp_max: Optional[float] = None,
        hbd_max: Optional[int] = None,
        hba_max: Optional[int] = None,
        tpsa_max: Optional[float] = None,
        rotatable_bonds_max: Optional[int] = None,
        fields: Optional[str] = "inchikey,pubchem,chembl,drugbank,name",
        size: Optional[int] = 10
    ) -> Dict[str, Any]:
        """Search chemicals by molecular property ranges (Lipinski's Rule of Five, etc.)."""
        query_parts = []
        
        if mw_min is not None or mw_max is not None:
            mw_min_val = mw_min if mw_min is not None else "*"
            mw_max_val = mw_max if mw_max is not None else "*"
            query_parts.append(f"pubchem.molecular_weight:[{mw_min_val} TO {mw_max_val}]")
        
        if logp_min is not None or logp_max is not None:
            logp_min_val = logp_min if logp_min is not None else "*"
            logp_max_val = logp_max if logp_max is not None else "*"
            query_parts.append(f"pubchem.xlogp:[{logp_min_val} TO {logp_max_val}]")
        
        if hbd_max is not None:
            query_parts.append(f"pubchem.h_bond_donor_count:[* TO {hbd_max}]")
        
        if hba_max is not None:
            query_parts.append(f"pubchem.h_bond_acceptor_count:[* TO {hba_max}]")
        
        if tpsa_max is not None:
            query_parts.append(f"pubchem.tpsa:[* TO {tpsa_max}]")
        
        if rotatable_bonds_max is not None:
            query_parts.append(f"pubchem.rotatable_bond_count:[* TO {rotatable_bonds_max}]")
        
        if not query_parts:
            raise ValueError("At least one molecular property filter must be specified")
        
        q = " AND ".join(query_parts)
        
        return await self.search_chemical(
            client=client,
            q=q,
            fields=fields,
            size=size
        )
    
    async def build_complex_query(
        self,
        client: MyChemClient,
        criteria: List[Dict[str, Any]],
        logic: str = "AND",
        fields: Optional[str] = "inchikey,pubchem,chembl,drugbank,name",
        size: Optional[int] = 10
    ) -> Dict[str, Any]:
        """Build complex queries with multiple criteria.
        
        Example criteria:
        [
            {"type": "field", "field": "drugbank.groups", "value": "approved"},
            {"type": "range", "field": "pubchem.molecular_weight", "min": 150, "max": 500},
            {"type": "exists", "field": "chembl.max_phase"},
            {"type": "text", "value": "inhibitor"}
        ]
        """
        query_parts = []
        
        for criterion in criteria:
            criterion_type = criterion.get("type")
            
            if criterion_type == "field":
                field = criterion["field"]
                value = criterion["value"]
                if " " in str(value) and not (str(value).startswith('"') and str(value).endswith('"')):
                    value = f'"{value}"'
                query_parts.append(f"{field}:{value}")
            
            elif criterion_type == "range":
                field = criterion["field"]
                min_val = criterion.get("min", "*")
                max_val = criterion.get("max", "*")
                query_parts.append(f"{field}:[{min_val} TO {max_val}]")
            
            elif criterion_type == "exists":
                field = criterion["field"]
                query_parts.append(f"_exists_:{field}")
            
            elif criterion_type == "text":
                value = criterion["value"]
                query_parts.append(value)
            
            else:
                raise ValueError(f"Unknown criterion type: {criterion_type}")
        
        q = f" {logic} ".join(query_parts)
        
        return await self.search_chemical(
            client=client,
            q=q,
            fields=fields,
            size=size
        )

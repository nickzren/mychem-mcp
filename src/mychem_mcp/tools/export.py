# src/mychem_mcp/tools/export.py
"""Enhanced data export tools."""

import csv
import io
import json
from typing import Any, Dict, List, Optional

from ..client import MyChemClient


class ExportApi:
    """Enhanced tools for exporting chemical data."""

    @staticmethod
    def _normalize_records(results: Any) -> List[Dict[str, Any]]:
        if isinstance(results, list):
            return [item for item in results if isinstance(item, dict)]
        if isinstance(results, dict):
            return [results]
        return []

    @staticmethod
    def _extract_compound_name(record: Dict[str, Any]) -> str:
        return (
            record.get("name")
            or record.get("drugbank", {}).get("name")
            or record.get("chembl", {}).get("pref_name")
            or ""
        )

    @staticmethod
    def _extract_compound_id(record: Dict[str, Any]) -> str:
        return record.get("inchikey") or record.get("_id") or record.get("query") or ""
    
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

        raw_results = await client.post("chem", post_data)
        results = self._normalize_records(raw_results)
        
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
                sdf_output.append(self._extract_compound_id(chem))
                sdf_output.append("")
                sdf_output.append(f"> <NAME>")
                sdf_output.append(self._extract_compound_name(chem))
                sdf_output.append("")
                sdf_output.append("$$$$")
            
            return "\n".join(sdf_output)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def export_filtered_dataset(
        self,
        client: MyChemClient,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        format: str = "csv",
        fields: Optional[List[str]] = None,
        max_results: int = 10000,
        batch_size: int = 1000
    ) -> str:
        """Export large filtered datasets with pagination."""
        if not fields:
            fields = ["inchikey", "name", "pubchem.cid", "chembl.molecule_chembl_id", 
                     "drugbank.id", "molecular_formula", "molecular_weight"]
        
        fields_str = ",".join(fields)
        
        # Build query with filters
        query_parts = [query]
        for field, value in (filters or {}).items():
            if isinstance(value, dict):
                # Range query
                if "min" in value or "max" in value:
                    min_val = value.get("min", "*")
                    max_val = value.get("max", "*")
                    query_parts.append(f"{field}:[{min_val} TO {max_val}]")
            else:
                # Exact match
                query_parts.append(f'{field}:"{value}"')
        
        final_query = " AND ".join(query_parts)
        
        # Collect all results with pagination
        all_results = []
        offset = 0
        
        while offset < max_results:
            params = {
                "q": final_query,
                "fields": fields_str,
                "size": min(batch_size, max_results - offset),
                "from": offset
            }
            
            result = await client.get("query", params=params)
            hits = result.get("hits", [])
            
            if not hits:
                break
            
            all_results.extend(hits)
            offset += len(hits)
            
            # Check if we've retrieved all available results
            if offset >= result.get("total", 0):
                break
        
        # Format results
        if format == "json":
            return json.dumps(all_results, indent=2)
        
        elif format in ["csv", "tsv"]:
            # Flatten results
            flattened = []
            for hit in all_results:
                flat_hit = {"_id": hit.get("_id"), "_score": hit.get("_score")}
                
                for field in fields:
                    if "." in field:
                        parts = field.split(".")
                        value = hit
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                value = None
                                break
                        flat_hit[field] = value
                    else:
                        flat_hit[field] = hit.get(field)
                
                flattened.append(flat_hit)
            
            # Create output
            output = io.StringIO()
            delimiter = "\t" if format == "tsv" else ","
            
            all_fields = ["_id", "_score"] + fields
            writer = csv.DictWriter(output, fieldnames=all_fields, delimiter=delimiter)
            
            writer.writeheader()
            writer.writerows(flattened)
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def export_compound_comparison(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        comparison_fields: List[str],
        format: str = "csv"
    ) -> str:
        """Export a comparison table of multiple compounds."""
        # Default comparison fields if not specified
        if not comparison_fields:
            comparison_fields = [
                "name",
                "molecular_formula",
                "molecular_weight",
                "xlogp",
                "tpsa",
                "h_bond_donor_count",
                "h_bond_acceptor_count",
                "rotatable_bond_count",
                "drugbank.groups",
                "chembl.max_phase",
                "ro5_violations"
            ]
        
        # Build fields list
        all_fields = set(["inchikey"])
        for field in comparison_fields:
            if "." in field:
                # For nested fields, we need the parent
                all_fields.add(field)
            else:
                # Map common names to actual fields
                field_map = {
                    "name": "drugbank.name,chembl.pref_name",
                    "molecular_formula": "pubchem.molecular_formula",
                    "molecular_weight": "pubchem.molecular_weight",
                    "xlogp": "pubchem.xlogp",
                    "tpsa": "pubchem.tpsa",
                    "h_bond_donor_count": "pubchem.h_bond_donor_count",
                    "h_bond_acceptor_count": "pubchem.h_bond_acceptor_count",
                    "rotatable_bond_count": "pubchem.rotatable_bond_count",
                    "ro5_violations": "chembl.num_ro5_violations"
                }
                all_fields.add(field_map.get(field, field))
        
        # Fetch data for all compounds
        post_data = {
            "ids": chemical_ids,
            "fields": ",".join(all_fields)
        }

        raw_results = await client.post("chem", post_data)
        results = self._normalize_records(raw_results)
        
        # Create comparison matrix
        comparison_data = []
        
        for result in results:
            row = {"inchikey": result.get("_id", result.get("query", "Unknown"))}
            
            # Extract comparison fields
            for field in comparison_fields:
                value = None
                
                if field == "name":
                    value = (result.get("drugbank", {}).get("name") or
                            result.get("chembl", {}).get("pref_name"))
                elif field in ["molecular_formula", "molecular_weight", "xlogp", "tpsa",
                             "h_bond_donor_count", "h_bond_acceptor_count", "rotatable_bond_count"]:
                    value = result.get("pubchem", {}).get(field)
                elif field == "drugbank.groups":
                    groups = result.get("drugbank", {}).get("groups", [])
                    value = ", ".join(groups) if isinstance(groups, list) else groups
                elif field == "chembl.max_phase":
                    value = result.get("chembl", {}).get("max_phase")
                elif field == "ro5_violations":
                    value = result.get("chembl", {}).get("num_ro5_violations")
                elif "." in field:
                    # Handle arbitrary nested fields
                    parts = field.split(".")
                    temp_value = result
                    for part in parts:
                        if isinstance(temp_value, dict) and part in temp_value:
                            temp_value = temp_value[part]
                        else:
                            temp_value = None
                            break
                    value = temp_value
                
                row[field] = value
            
            comparison_data.append(row)
        
        # Format output
        if format == "json":
            return json.dumps(comparison_data, indent=2)
        
        elif format in ["csv", "tsv"]:
            output = io.StringIO()
            delimiter = "\t" if format == "tsv" else ","
            
            fieldnames = ["inchikey"] + comparison_fields
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
            
            writer.writeheader()
            writer.writerows(comparison_data)
            
            return output.getvalue()
        
        elif format == "markdown":
            # Create markdown table
            lines = []
            
            # Header
            headers = ["InChIKey"] + [f.replace("_", " ").title() for f in comparison_fields]
            lines.append("| " + " | ".join(headers) + " |")
            lines.append("|" + "|".join(["-" * (len(h) + 2) for h in headers]) + "|")
            
            # Data rows
            for row in comparison_data:
                values = [str(row.get("inchikey", ""))]
                for field in comparison_fields:
                    val = row.get(field, "")
                    values.append(str(val) if val is not None else "")
                lines.append("| " + " | ".join(values) + " |")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    async def export_activity_profile(
        self,
        client: MyChemClient,
        chemical_id: str,
        format: str = "json"
    ) -> str:
        """Export comprehensive activity profile for a chemical."""
        # Fetch comprehensive data
        fields = [
            "inchikey",
            "drugbank.name",
            "chembl.pref_name",
            "pubchem.molecular_formula",
            "pubchem.molecular_weight",
            "chembl.activities",
            "drugbank.targets",
            "drugbank.enzymes",
            "drugbank.indication",
            "chembl.max_phase",
            "drugbank.groups"
        ]
        
        params = {"fields": ",".join(fields)}
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        # Build activity profile
        profile = {
            "chemical_id": chemical_id,
            "basic_info": {
                "name": (result.get("drugbank", {}).get("name") or
                        result.get("chembl", {}).get("pref_name")),
                "formula": result.get("pubchem", {}).get("molecular_formula"),
                "molecular_weight": result.get("pubchem", {}).get("molecular_weight"),
                "development_phase": result.get("chembl", {}).get("max_phase"),
                "approval_status": result.get("drugbank", {}).get("groups", [])
            },
            "therapeutic_info": {
                "indication": result.get("drugbank", {}).get("indication")
            },
            "targets": [],
            "activities": [],
            "enzymes": []
        }
        
        # Process targets
        if "drugbank" in result and "targets" in result["drugbank"]:
            targets = result["drugbank"]["targets"]
            if not isinstance(targets, list):
                targets = [targets]
            profile["targets"] = targets
        
        # Process activities
        if "chembl" in result and "activities" in result["chembl"]:
            activities = result["chembl"]["activities"]
            if not isinstance(activities, list):
                activities = [activities]
            
            # Group activities by target
            activity_summary = {}
            for act in activities:
                target = act.get("target_pref_name", "Unknown")
                act_type = act.get("standard_type", "Unknown")
                
                if target not in activity_summary:
                    activity_summary[target] = []
                
                activity_summary[target].append({
                    "type": act_type,
                    "value": act.get("standard_value"),
                    "units": act.get("standard_units"),
                    "assay": act.get("assay_chembl_id")
                })
            
            profile["activities"] = activity_summary
        
        # Process enzymes
        if "drugbank" in result and "enzymes" in result["drugbank"]:
            enzymes = result["drugbank"]["enzymes"]
            if not isinstance(enzymes, list):
                enzymes = [enzymes]
            profile["enzymes"] = enzymes
        
        # Format output
        if format == "json":
            return json.dumps(profile, indent=2)
        
        elif format == "markdown":
            lines = []
            
            # Header
            lines.append(f"# Activity Profile: {profile['basic_info']['name'] or chemical_id}")
            lines.append("")
            
            # Basic info
            lines.append("## Basic Information")
            for key, value in profile["basic_info"].items():
                if value:
                    lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")
            lines.append("")
            
            # Therapeutic info
            if profile["therapeutic_info"]["indication"]:
                lines.append("## Therapeutic Information")
                lines.append(f"**Indication**: {profile['therapeutic_info']['indication']}")
                lines.append("")
            
            # Targets
            if profile["targets"]:
                lines.append("## Targets")
                for target in profile["targets"]:
                    lines.append(f"- {target.get('name', 'Unknown')} ({target.get('gene_name', 'N/A')})")
                lines.append("")
            
            # Activities
            if profile["activities"]:
                lines.append("## Bioactivities")
                for target, activities in profile["activities"].items():
                    lines.append(f"### {target}")
                    for act in activities:
                        lines.append(f"- {act['type']}: {act['value']} {act['units']}")
                    lines.append("")
            
            return "\n".join(lines)
        
        else:
            raise ValueError(f"Unsupported format: {format}")

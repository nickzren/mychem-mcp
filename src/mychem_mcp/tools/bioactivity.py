# src/mychem_mcp/tools/bioactivity.py
"""Bioactivity and assay data tools."""

from typing import Any, Dict, Optional, List

from ..client import MyChemClient


class BioactivityApi:
    """Tools for bioactivity and assay data."""
    
    async def get_bioassay_data(
        self,
        client: MyChemClient,
        chemical_id: str,
        activity_type: Optional[str] = None,
        target_type: Optional[str] = None,
        min_potency: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get bioactivity/assay results for a chemical."""
        # Build fields based on filters
        fields = []
        fields.append("chembl.activities")
        fields.append("pubchem.bioassays")
        fields.append("drugbank.experimental_properties")
        
        params = {"fields": ",".join(fields)}
        
        result = await client.get(f"chem/{chemical_id}", params=params)
        
        bioassay_data = {
            "chemical_id": chemical_id,
            "activities": [],
            "assay_summary": {
                "total_assays": 0,
                "active_assays": 0,
                "target_types": {},
                "activity_types": {}
            }
        }
        
        # Process ChEMBL activities
        if "chembl" in result and "activities" in result["chembl"]:
            activities = result["chembl"]["activities"]
            if not isinstance(activities, list):
                activities = [activities]
            
            for activity in activities:
                # Apply filters
                if activity_type and activity.get("standard_type") != activity_type:
                    continue
                if target_type and activity.get("target_type") != target_type:
                    continue
                if min_potency is not None and activity.get("standard_value") is not None:
                    try:
                        if float(activity["standard_value"]) > min_potency:
                            continue
                    except (TypeError, ValueError):
                        continue
                
                processed_activity = {
                    "source": "chembl",
                    "assay_id": activity.get("assay_chembl_id"),
                    "target_name": activity.get("target_pref_name"),
                    "target_type": activity.get("target_type"),
                    "activity_type": activity.get("standard_type"),
                    "value": activity.get("standard_value"),
                    "units": activity.get("standard_units"),
                    "relation": activity.get("standard_relation"),
                    "activity_comment": activity.get("activity_comment")
                }
                
                bioassay_data["activities"].append(processed_activity)
                
                # Update summary
                bioassay_data["assay_summary"]["total_assays"] += 1
                if activity.get("standard_relation") == "=":
                    bioassay_data["assay_summary"]["active_assays"] += 1
                
                # Count target types
                tt = activity.get("target_type", "Unknown")
                bioassay_data["assay_summary"]["target_types"][tt] = \
                    bioassay_data["assay_summary"]["target_types"].get(tt, 0) + 1
                
                # Count activity types
                at = activity.get("standard_type", "Unknown")
                bioassay_data["assay_summary"]["activity_types"][at] = \
                    bioassay_data["assay_summary"]["activity_types"].get(at, 0) + 1
        
        # Process PubChem bioassays
        if "pubchem" in result and "bioassays" in result["pubchem"]:
            bioassays = result["pubchem"]["bioassays"]
            if not isinstance(bioassays, list):
                bioassays = [bioassays]
            
            for assay in bioassays:
                processed_assay = {
                    "source": "pubchem",
                    "assay_id": f"AID{assay.get('aid')}",
                    "assay_name": assay.get("name"),
                    "activity_outcome": assay.get("activity_outcome"),
                    "assay_type": assay.get("assay_type")
                }
                
                bioassay_data["activities"].append(processed_assay)
                bioassay_data["assay_summary"]["total_assays"] += 1
                if assay.get("activity_outcome") == "Active":
                    bioassay_data["assay_summary"]["active_assays"] += 1
        
        return {
            "success": True,
            "bioassay_data": bioassay_data
        }
    
    async def search_active_compounds(
        self,
        client: MyChemClient,
        target_name: str,
        activity_type: str = "IC50",
        max_value: float = 1000,
        units: str = "nM",
        size: int = 10
    ) -> Dict[str, Any]:
        """Search for compounds active against a specific target."""
        # Build query for active compounds
        query_parts = [
            f'chembl.activities.target_pref_name:"{target_name}"',
            f'chembl.activities.standard_type:{activity_type}',
            f'chembl.activities.standard_units:{units}',
            f'chembl.activities.standard_value:[* TO {max_value}]'
        ]
        
        q = " AND ".join(query_parts)
        
        params = {
            "q": q,
            "fields": "inchikey,chembl,drugbank.name,chembl.activities",
            "size": size
        }
        
        result = await client.get("query", params=params)
        
        # Process hits to extract relevant activities
        active_compounds = []
        for hit in result.get("hits", []):
            compound = {
                "inchikey": hit.get("_id"),
                "chembl_id": hit.get("chembl", {}).get("molecule_chembl_id"),
                "name": hit.get("drugbank", {}).get("name"),
                "relevant_activities": []
            }
            
            # Extract matching activities
            if "chembl" in hit and "activities" in hit["chembl"]:
                activities = hit["chembl"]["activities"]
                if not isinstance(activities, list):
                    activities = [activities]
                
                for activity in activities:
                    if (activity.get("target_pref_name") == target_name and
                        activity.get("standard_type") == activity_type and
                        activity.get("standard_units") == units):
                        try:
                            value = float(activity.get("standard_value", 0))
                            if value <= max_value:
                                compound["relevant_activities"].append({
                                    "value": value,
                                    "units": units,
                                    "assay_id": activity.get("assay_chembl_id")
                                })
                        except (TypeError, ValueError):
                            pass
            
            if compound["relevant_activities"]:
                active_compounds.append(compound)
        
        return {
            "success": True,
            "query": {
                "target": target_name,
                "activity_type": activity_type,
                "threshold": f"{max_value} {units}"
            },
            "total_found": len(active_compounds),
            "active_compounds": active_compounds
        }
    
    async def compare_compound_activities(
        self,
        client: MyChemClient,
        chemical_ids: List[str],
        target_name: Optional[str] = None,
        activity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Compare bioactivities across multiple compounds."""
        if not activity_types:
            activity_types = ["IC50", "EC50", "Ki", "Kd"]
        
        # Fetch activities for all compounds
        fields = "chembl.activities,drugbank.name,chembl.pref_name"
        
        comparison_data = {
            "compounds": [],
            "activity_matrix": {},
            "target_summary": {}
        }
        
        for chem_id in chemical_ids:
            result = await client.get(f"chem/{chem_id}", params={"fields": fields})
            
            compound_data = {
                "chemical_id": chem_id,
                "name": (result.get("drugbank", {}).get("name") or 
                        result.get("chembl", {}).get("pref_name")),
                "activities_by_target": {}
            }
            
            if "chembl" in result and "activities" in result["chembl"]:
                activities = result["chembl"]["activities"]
                if not isinstance(activities, list):
                    activities = [activities]
                
                for activity in activities:
                    # Filter by target if specified
                    if target_name and activity.get("target_pref_name") != target_name:
                        continue
                    
                    # Filter by activity type
                    if activity.get("standard_type") not in activity_types:
                        continue
                    
                    target = activity.get("target_pref_name", "Unknown")
                    act_type = activity.get("standard_type")
                    
                    if target not in compound_data["activities_by_target"]:
                        compound_data["activities_by_target"][target] = {}
                    
                    if act_type and activity.get("standard_value"):
                        compound_data["activities_by_target"][target][act_type] = {
                            "value": activity.get("standard_value"),
                            "units": activity.get("standard_units"),
                            "assay_id": activity.get("assay_chembl_id")
                        }
                    
                    # Update target summary
                    if target not in comparison_data["target_summary"]:
                        comparison_data["target_summary"][target] = {
                            "compounds_tested": 0,
                            "activity_types": []
                        }
                    if (
                        act_type
                        and act_type
                        not in comparison_data["target_summary"][target]["activity_types"]
                    ):
                        comparison_data["target_summary"][target]["activity_types"].append(act_type)
            
            comparison_data["compounds"].append(compound_data)
        
        # Update compound counts in target summary
        for target in comparison_data["target_summary"]:
            count = sum(1 for comp in comparison_data["compounds"] 
                       if target in comp["activities_by_target"])
            comparison_data["target_summary"][target]["compounds_tested"] = count
        
        return {
            "success": True,
            "comparison": comparison_data
        }

# src/mychem_mcp/server.py
"""MyChem MCP Server implementation."""

import asyncio
import json
from typing import Any, Dict
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

from .client import MyChemClient
from .tools import (
    QUERY_TOOLS, QueryApi,
    ANNOTATION_TOOLS, AnnotationApi,
    BATCH_TOOLS, BatchApi,
    STRUCTURE_TOOLS, StructureApi,
    DRUG_TOOLS, DrugApi,
    ADMET_TOOLS, ADMETApi,
    PATENT_TOOLS, PatentApi,
    CLINICAL_TOOLS, ClinicalApi,
    METADATA_TOOLS, MetadataApi,
    EXPORT_TOOLS, ExportApi
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Combine all tools
ALL_TOOLS = (
    QUERY_TOOLS +
    ANNOTATION_TOOLS +
    BATCH_TOOLS +
    STRUCTURE_TOOLS +
    DRUG_TOOLS +
    ADMET_TOOLS +
    PATENT_TOOLS +
    CLINICAL_TOOLS +
    METADATA_TOOLS +
    EXPORT_TOOLS
)

# Create API class mapping
API_CLASS_MAP = {
    # Query tools
    "search_chemical": QueryApi,
    "search_by_field": QueryApi,
    "get_field_statistics": QueryApi,
    # Annotation tools
    "get_chemical_by_id": AnnotationApi,
    # Batch tools
    "batch_query_chemicals": BatchApi,
    "batch_get_chemicals": BatchApi,
    # Structure tools
    "get_chemical_structure": StructureApi,
    "search_by_structure": StructureApi,
    "convert_structure": StructureApi,
    # Drug tools
    "search_drug": DrugApi,
    "get_drug_interactions": DrugApi,
    "get_drug_targets": DrugApi,
    # ADMET tools
    "get_admet_properties": ADMETApi,
    "predict_toxicity": ADMETApi,
    # Patent tools
    "get_patent_data": PatentApi,
    "search_patents_by_chemical": PatentApi,
    # Clinical tools
    "get_clinical_trials": ClinicalApi,
    "get_fda_approval": ClinicalApi,
    # Metadata tools
    "get_mychem_metadata": MetadataApi,
    "get_available_fields": MetadataApi,
    "get_database_statistics": MetadataApi,
    # Export tools
    "export_chemical_list": ExportApi,
}


class MyChemMcpServer:
    """MCP Server for MyChemInfo data."""
    
    def __init__(self):
        self.server_name = "mychem-mcp"
        self.server_version = "0.2.0"
        self.mcp_server = Server(self.server_name, self.server_version)
        self.client = MyChemClient()
        self._api_instances: Dict[type, Any] = {}
        self._setup_handlers()
        logger.info(f"{self.server_name} v{self.server_version} initialized.")
    
    def _setup_handlers(self):
        """Register MCP handlers."""
        
        @self.mcp_server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Returns the list of all available tools."""
            return ALL_TOOLS
        
        @self.mcp_server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Dict[str, Any]
        ) -> list[types.TextContent]:
            """Handles a tool call request."""
            logger.info(f"Handling call for tool: '{name}'")
            
            try:
                if name not in API_CLASS_MAP:
                    raise ValueError(f"Unknown tool: {name}")
                
                api_class = API_CLASS_MAP[name]
                
                if api_class not in self._api_instances:
                    self._api_instances[api_class] = api_class()
                
                api_instance = self._api_instances[api_class]
                
                if not hasattr(api_instance, name):
                    raise ValueError(f"Tool method '{name}' not found")
                
                func_to_call = getattr(api_instance, name)
                result_data = await func_to_call(self.client, **arguments)
                
                # Handle export tools that return strings directly
                if isinstance(result_data, str):
                    return [types.TextContent(type="text", text=result_data)]
                
                result_json = json.dumps(result_data, indent=2)
                return [types.TextContent(type="text", text=result_json)]
            
            except Exception as e:
                logger.error(f"Error calling tool '{name}': {str(e)}", exc_info=True)
                error_response = {
                    "error": type(e).__name__,
                    "message": str(e),
                    "tool_name": name
                }
                return [types.TextContent(type="text", text=json.dumps(error_response, indent=2))]
    
    async def run(self):
        """Starts the MCP server."""
        logger.info(f"Starting {self.server_name} v{self.server_version}...")
        
        async with stdio_server() as (read_stream, write_stream):
            await self.mcp_server.run(
                read_stream, 
                write_stream,
                self.mcp_server.create_initialization_options()
            )


def main():
    """Main entry point."""
    server = MyChemMcpServer()
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user.")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
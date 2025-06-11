# src/mychem_mcp/client.py
"""MyChemInfo API client."""

import httpx
from typing import Any, Dict, Optional


class MyChemError(Exception):
    """Custom error for MyChem API operations."""
    pass


class MyChemClient:
    """Client for MyChemInfo API."""
    
    def __init__(self, base_url: str = "https://mychem.info/v1", timeout: float = 30.0):
        self.base_url = base_url
        self.timeout = timeout
    
    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to MyChem API."""
        url = f"{self.base_url}/{endpoint}"
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise MyChemError("Request timed out. Please try again.")
            except httpx.HTTPStatusError as e:
                raise MyChemError(f"HTTP error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise MyChemError(f"Request failed: {str(e)}")
    
    async def post(self, endpoint: str, json_data: Any) -> Any:
        """Make POST request to MyChem API."""
        url = f"{self.base_url}/{endpoint}"
        headers = {"content-type": "application/json"}
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, json=json_data, headers=headers, timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException:
                raise MyChemError("Request timed out. Please try again.")
            except httpx.HTTPStatusError as e:
                raise MyChemError(f"HTTP error {e.response.status_code}: {e.response.text}")
            except Exception as e:
                raise MyChemError(f"Request failed: {str(e)}")
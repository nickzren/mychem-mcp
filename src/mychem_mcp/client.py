# src/mychem_mcp/client.py
"""MyChemInfo API client with caching support."""

import asyncio
import json
from collections import OrderedDict
from datetime import datetime, timedelta
import hashlib
from typing import Any, Dict, Optional

import httpx


class MyChemError(Exception):
    """Custom error for MyChem API operations."""
    pass


class CacheEntry:
    """Cache entry with expiration."""
    
    def __init__(self, data: Any, ttl_seconds: int = 3600):
        self.data = data
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
    
    def is_expired(self) -> bool:
        return datetime.now() > self.expires_at


class MyChemClient:
    """Client for MyChemInfo API with optional caching."""

    def __init__(
        self,
        base_url: str = "https://mychem.info/v1",
        timeout: float = 30.0,
        cache_enabled: bool = True,
        cache_ttl: int = 3600,
        rate_limit: Optional[int] = 10,
        cache_max_entries: int = 5000,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.cache_ttl = cache_ttl
        self.rate_limit = rate_limit
        self.cache_max_entries = max(1, cache_max_entries)
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._cache_gc_interval = 250
        self._cache_set_ops = 0
        self._last_request_time = None
        self._request_count = 0
        self._http_client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    
    def _get_cache_key(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Any = None) -> str:
        """Generate cache key from request parameters."""
        key_parts = [method, endpoint]
        if params:
            key_parts.append(json.dumps(params, sort_keys=True))
        if data:
            key_parts.append(json.dumps(data, sort_keys=True))
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[Any]:
        """Check if valid cached response exists."""
        if not self.cache_enabled:
            return None

        entry = self._cache.get(cache_key)
        if entry is None:
            return None

        if entry.is_expired():
            self._cache.pop(cache_key, None)
            return None

        self._cache.move_to_end(cache_key)
        return entry.data

    def _prune_expired_cache(self) -> None:
        """Prune expired entries from cache."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
        for key in expired_keys:
            self._cache.pop(key, None)

    def _evict_lru_if_needed(self) -> None:
        """Evict least recently used entries to respect max cache size."""
        while len(self._cache) > self.cache_max_entries:
            self._cache.popitem(last=False)

    def _update_cache(self, cache_key: str, data: Any):
        """Update cache with new data."""
        if not self.cache_enabled:
            return

        self._cache_set_ops += 1
        if self._cache_set_ops % self._cache_gc_interval == 0:
            self._prune_expired_cache()

        self._cache[cache_key] = CacheEntry(data, self.cache_ttl)
        self._cache.move_to_end(cache_key)
        self._evict_lru_if_needed()

    def clear_cache(self):
        """Clear all cached entries."""
        self._cache.clear()

    async def _apply_rate_limit(self):
        """Apply rate limiting if configured."""
        if self.rate_limit and self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < 1.0:
                self._request_count += 1
                if self._request_count >= self.rate_limit:
                    sleep_time = 1.0 - elapsed
                    await asyncio.sleep(sleep_time)
                    self._request_count = 0
            else:
                self._request_count = 1
        else:
            self._request_count = 1

        self._last_request_time = datetime.now()

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to MyChem API with caching."""
        cache_key = self._get_cache_key("GET", endpoint, params)
        cached_data = self._check_cache(cache_key)
        if cached_data is not None:
            return cached_data

        await self._apply_rate_limit()

        url = f"{self.base_url}/{endpoint}"
        try:
            response = await self._http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            self._update_cache(cache_key, data)
            return data
        except httpx.TimeoutException:
            raise MyChemError("Request timed out. Please try again.")
        except httpx.HTTPStatusError as e:
            raise MyChemError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise MyChemError(f"Request failed: {str(e)}")

    async def post(self, endpoint: str, json_data: Any, use_cache: bool = True) -> Any:
        """Make POST request to MyChem API with optional caching."""
        cache_key = self._get_cache_key("POST", endpoint, data=json_data)
        if use_cache:
            cached_data = self._check_cache(cache_key)
            if cached_data is not None:
                return cached_data

        await self._apply_rate_limit()

        url = f"{self.base_url}/{endpoint}"
        headers = {"content-type": "application/json"}
        try:
            response = await self._http_client.post(url, json=json_data, headers=headers)
            response.raise_for_status()
            data = response.json()
            if use_cache:
                self._update_cache(cache_key, data)
            return data
        except httpx.TimeoutException:
            raise MyChemError("Request timed out. Please try again.")
        except httpx.HTTPStatusError as e:
            raise MyChemError(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise MyChemError(f"Request failed: {str(e)}")

    async def close(self) -> None:
        """Close persistent HTTP client resources."""
        await self._http_client.aclose()

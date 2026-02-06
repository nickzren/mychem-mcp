# tests/test_client.py
"""Tests for MyChem client internals."""

import pytest

from mychem_mcp.client import CacheEntry, MyChemClient


class TestMyChemClient:
    """Test cache and lifecycle behavior in MyChemClient."""

    @pytest.mark.asyncio
    async def test_cache_respects_max_entries_with_lru_eviction(self):
        """Least recently used cache entry should be evicted when full."""
        client = MyChemClient(cache_enabled=True, cache_ttl=60, cache_max_entries=2)
        try:
            client._update_cache("a", {"value": 1})
            client._update_cache("b", {"value": 2})

            # Mark "a" as recently used; "b" should become LRU.
            assert client._check_cache("a") == {"value": 1}
            client._update_cache("c", {"value": 3})

            assert "a" in client._cache
            assert "b" not in client._cache
            assert "c" in client._cache
        finally:
            await client.close()

    @pytest.mark.asyncio
    async def test_close_closes_underlying_http_client(self):
        """close() should close the persistent AsyncClient."""
        client = MyChemClient()
        assert client._http_client.is_closed is False
        await client.close()
        assert client._http_client.is_closed is True

    def test_cache_entry_expiration(self):
        """CacheEntry should report expiration correctly."""
        entry = CacheEntry(data={"x": 1}, ttl_seconds=0)
        assert entry.is_expired() is True

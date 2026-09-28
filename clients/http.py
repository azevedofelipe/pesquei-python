"""Shared `httpx` async client wrapper for outbound calls to external APIs.

One place to keep base URL, timeout, and retry config consistent across every
external API integration (Open-Meteo today, possibly others later) instead of
each integration module reinventing its own `httpx.AsyncClient` setup.

Usage:

    from clients.http import build_async_client

    async def call_something():
        async with build_async_client("https://api.example.com") as client:
            response = await client.get("/path", params={...})
            response.raise_for_status()
            return response.json()
"""

import httpx

# Conservative defaults: external weather/tide-style APIs are not
# latency-critical for the caller (the catch record is created either way),
# so a slightly generous timeout is fine, but we still don't want a single
# slow external call to hang a request indefinitely.
DEFAULT_TIMEOUT = httpx.Timeout(10.0, connect=5.0)

# httpx's built-in transport-level retry only retries on connection-level
# failures (DNS errors, connection resets, etc.), not on HTTP error status
# codes — that's a deliberate, safe default: retrying a 4xx/5xx response
# automatically could double-submit or hammer a rate-limited endpoint.
DEFAULT_RETRIES = 2


def build_async_client(
    base_url: str,
    timeout: httpx.Timeout | float = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
) -> httpx.AsyncClient:
    """Build an `httpx.AsyncClient` pre-configured with a base URL, timeout,
    and connection-level retry policy.

    Callers are responsible for using this as an async context manager (or
    closing it themselves) so the underlying connection pool is released:

        async with build_async_client(BASE_URL) as client:
            ...
    """
    transport = httpx.AsyncHTTPTransport(retries=retries)
    return httpx.AsyncClient(base_url=base_url, timeout=timeout, transport=transport)

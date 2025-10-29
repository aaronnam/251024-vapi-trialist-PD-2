# Unleash Intercom Source Filtering Implementation Guide

## Overview
This guide provides an elegant solution to filter Unleash search results to only the "Intercom" source in your LiveKit voice agent, maintaining compliance with LiveKit Agent SDK patterns.

## Current Implementation Analysis

Your current `unleash_search_knowledge` function (lines 266-427 in `agent.py`) searches across all available sources. The Unleash API supports filtering by `appId` to restrict results to specific sources.

## Solution Approach

### 1. Environment Configuration
Add the Intercom source ID to your environment variables for clean configuration management:

```bash
# In .env.local
UNLEASH_INTERCOM_APP_ID="<intercom-app-id>"  # You'll need to obtain this from Unleash
```

### 2. Update the Function Tool

Modify the `unleash_search_knowledge` function to automatically filter to Intercom:

```python
@function_tool()
async def unleash_search_knowledge(
    self,
    context: RunContext,
    query: str,
    category: Optional[str] = None,
    response_format: Optional[str] = None,
) -> Dict[str, Any]:
    """Search PandaDoc knowledge base from Intercom source.

    THIS IS A MANDATORY TOOL. You MUST call this for:
    - ANY question starting with: how, what, when, where, why, can, does, is
    - ANY mention of: documents, templates, signing, sending, pricing, features, integrations
    - ANY request for help, guidance, or troubleshooting
    - LITERALLY ANYTHING related to PandaDoc functionality

    DO NOT attempt to answer from memory. ALWAYS search first.

    Args:
        query: The user's exact question - pass it VERBATIM, do not modify
        category: Optional - ONLY for "features", "pricing", "integrations", or "troubleshooting"
        response_format: Use "concise" (default) for voice - never use "detailed"

    Returns:
        Dict with search results from Intercom knowledge base
    """

    # Validate and normalize response_format
    if not response_format or response_format not in ["concise", "detailed"]:
        if response_format:
            logger.warning(
                f"Invalid response_format '{response_format}', defaulting to 'concise'"
            )
        response_format = "concise"

    try:
        # Get Unleash configuration
        unleash_api_key = os.getenv("UNLEASH_API_KEY")
        if not unleash_api_key:
            raise ToolError(
                "PandaDoc knowledge base is not configured. Let me help you directly instead."
            )

        unleash_base_url = os.getenv("UNLEASH_BASE_URL", "https://e-api.unleash.so")
        unleash_assistant_id = os.getenv("UNLEASH_ASSISTANT_ID")  # Optional

        # Get Intercom app ID - CRITICAL for source filtering
        intercom_app_id = os.getenv("UNLEASH_INTERCOM_APP_ID")
        if not intercom_app_id:
            logger.warning("Intercom app ID not configured, searching all sources")

        # Build request payload with Intercom source filter
        request_payload = {
            "query": query,
            "contentSearch": True,  # Search content, not just titles
            "semanticSearch": True,  # Enable AI-powered semantic search
            "paging": {
                "pageSize": 3 if response_format == "concise" else 5,
                "pageNumber": 0,
            },
        }

        # Add filters - combine category and source filtering
        filters = {}

        # Add Intercom source filter if configured
        if intercom_app_id:
            filters["appId"] = [intercom_app_id]
            logger.info(f"Filtering search to Intercom source: {intercom_app_id}")

        # Add category filter if provided
        if category:
            filters["type"] = [category]

        # Only add filters to payload if we have any
        if filters:
            request_payload["filters"] = filters

        # Add assistant ID if configured
        if unleash_assistant_id:
            request_payload["assistantId"] = unleash_assistant_id

        # Make API request with proper error handling
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{unleash_base_url}/search",
                headers={
                    "Authorization": f"Bearer {unleash_api_key}",
                    "Content-Type": "application/json",
                },
                json=request_payload,
                timeout=10.0,
            )

            # [Rest of error handling and response processing remains the same...]
```

### 3. Alternative: Hardcoded Filtering (If App ID is Static)

If the Intercom app ID never changes, you can hardcode it for simplicity:

```python
# At the top of your agent class or as a class constant
INTERCOM_APP_ID = "your-intercom-app-id-here"  # Replace with actual ID

# Then in the function, simply use:
filters = {"appId": [INTERCOM_APP_ID]}
```

## Finding the Intercom App ID

To find the Intercom app ID in Unleash:

1. **Via API**: Use the `/filters/stats` endpoint to get available filter values:
```python
# Quick script to find app IDs
import httpx
import os
from dotenv import load_dotenv

load_dotenv(".env.local")

async def get_app_ids():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://e-api.unleash.so/filters/stats",
            headers={
                "Authorization": f"Bearer {os.getenv('UNLEASH_API_KEY')}",
                "Content-Type": "application/json",
            },
            json={"assistantId": os.getenv("UNLEASH_ASSISTANT_ID")}
        )
        data = response.json()
        # Look for appId filter values
        print("Available app IDs:", data.get("availableFilters", {}).get("appId", []))
```

2. **Via Unleash UI**: Navigate to your assistant configuration in Unleash and check the available data sources. The Intercom source should have an associated ID.

## Benefits of This Approach

1. **Clean Configuration**: Source filtering is handled via environment variables, making it easy to change without code modifications
2. **Graceful Fallback**: If the Intercom ID isn't configured, the agent searches all sources (with a logged warning)
3. **LiveKit Compliant**: Uses standard function_tool patterns without over-engineering
4. **Minimal Changes**: Only modifies the search payload construction, keeping all other logic intact
5. **Logging**: Adds informative logging to track when Intercom filtering is active

## Testing the Implementation

1. **Console Testing**:
```bash
cd my-app
uv run python src/agent.py console

# Test queries:
# "How do I create a template?"
# "What integrations are available?"
```

2. **Verify Filtering**: Check logs for "Filtering search to Intercom source" messages

3. **Unit Test Example**:
```python
import pytest
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_intercom_filtering():
    agent = PandaDocTrialistAgent()

    with patch.dict(os.environ, {"UNLEASH_INTERCOM_APP_ID": "intercom-123"}):
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"results": [], "totalResults": 0}

            await agent.unleash_search_knowledge(None, "test query")

            # Verify the request included Intercom filter
            call_args = mock_post.call_args
            request_body = call_args.kwargs["json"]
            assert "filters" in request_body
            assert request_body["filters"]["appId"] == ["intercom-123"]
```

## Deployment Checklist

- [ ] Obtain the Intercom app ID from Unleash
- [ ] Add `UNLEASH_INTERCOM_APP_ID` to `.env.local` for local development
- [ ] Add the secret to LiveKit Cloud for production deployment
- [ ] Update the function implementation with filtering logic
- [ ] Test in console mode to verify Intercom-only results
- [ ] Run existing tests to ensure no regressions
- [ ] Deploy to LiveKit Cloud with the new environment variable

## Notes

- The Unleash API supports multiple app IDs in the filter array, so you could extend this to search multiple specific sources if needed
- Consider adding a tool parameter to optionally override the source filter for flexibility
- Monitor search result quality after filtering to ensure Intercom source has sufficient coverage
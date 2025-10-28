#!/usr/bin/env python
"""
Script to find the Intercom app ID in Unleash.
Run from the my-app directory: uv run python scripts/find_intercom_id.py
"""

import asyncio
import json
import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env.local"
load_dotenv(env_path)


async def find_intercom_app_id():
    """Find the Intercom app ID using various Unleash API endpoints."""

    api_key = os.getenv("UNLEASH_API_KEY")
    base_url = os.getenv("UNLEASH_BASE_URL", "https://e-api.unleash.so")
    assistant_id = os.getenv("UNLEASH_ASSISTANT_ID")

    if not api_key:
        print("❌ UNLEASH_API_KEY not found in .env.local")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print("🔍 Searching for Intercom source ID...\n")

    async with httpx.AsyncClient() as client:
        # Method 1: Search for Intercom-related content
        print("Method 1: Searching for Intercom content...")
        try:
            search_payload = {
                "query": "Intercom",
                "contentSearch": True,
                "paging": {"pageSize": 1, "pageNumber": 0}
            }
            if assistant_id:
                search_payload["assistantId"] = assistant_id

            response = await client.post(
                f"{base_url}/search",
                headers=headers,
                json=search_payload,
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    resource = result.get("resource", {})

                    # Look for app-related fields
                    print(f"  Found resource: {resource.get('title', 'Unknown')}")

                    # Check various possible field names
                    possible_fields = ["appId", "app_id", "sourceId", "source_id", "appInstance", "app"]
                    for field in possible_fields:
                        if field in resource:
                            print(f"  ✅ Found {field}: {resource[field]}")

                    # Pretty print the full resource to see all fields
                    print("\n  Full resource metadata:")
                    print(f"  {json.dumps(resource, indent=2)[:500]}...")  # First 500 chars
        except Exception as e:
            print(f"  ⚠️  Search failed: {e}")

        # Method 2: Try the filters/stats endpoint
        print("\nMethod 2: Checking filter statistics...")
        try:
            stats_payload = {}
            if assistant_id:
                stats_payload["assistantId"] = assistant_id

            response = await client.post(
                f"{base_url}/filters/stats",
                headers=headers,
                json=stats_payload,
                timeout=10.0
            )

            if response.status_code == 200:
                data = response.json()
                available_filters = data.get("availableFilters", {})

                # Look for appId in available filters
                if "appId" in available_filters:
                    app_ids = available_filters["appId"]
                    print(f"  Found {len(app_ids)} app IDs available:")
                    for app_id in app_ids:
                        # Check if this might be Intercom based on the ID pattern
                        if "intercom" in str(app_id).lower():
                            print(f"  ✅ Likely Intercom ID: {app_id}")
                        else:
                            print(f"  - {app_id}")
                else:
                    print("  No appId filter found in stats")

                # Also check for app-related fields
                for key in available_filters:
                    if "app" in key.lower() or "source" in key.lower():
                        print(f"  Found filter '{key}': {available_filters[key][:3]}...")  # First 3 values

        except Exception as e:
            print(f"  ⚠️  Stats query failed: {e}")

        # Method 3: Search with different queries to find patterns
        print("\nMethod 3: Pattern matching in search results...")
        test_queries = ["", "PandaDoc", "help", "article"]

        for query in test_queries[:2]:  # Test first 2 to avoid too many requests
            try:
                search_payload = {
                    "query": query if query else "test",
                    "contentSearch": True,
                    "paging": {"pageSize": 2, "pageNumber": 0}
                }
                if assistant_id:
                    search_payload["assistantId"] = assistant_id

                response = await client.post(
                    f"{base_url}/search",
                    headers=headers,
                    json=search_payload,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("results", []):
                        resource = result.get("resource", {})
                        # Look for patterns that might indicate source
                        for key, value in resource.items():
                            if "intercom" in str(value).lower():
                                print(f"  Found 'intercom' in {key}: {value}")
                            if key in ["appId", "sourceId", "app", "source"]:
                                print(f"  Found {key}: {value}")

            except Exception as e:
                print(f"  ⚠️  Query '{query}' failed: {e}")

    print("\n" + "="*50)
    print("💡 Tips:")
    print("1. If you see multiple app IDs above, the Intercom one likely contains 'intercom' in the ID")
    print("2. You can also check the Unleash dashboard by clicking on the Intercom source")
    print("3. The app ID might be a GUID or a simple string like 'intercom'")
    print("\nOnce you identify the correct ID, add it to your .env.local file:")
    print("UNLEASH_INTERCOM_APP_ID=<the-id-you-found>")


if __name__ == "__main__":
    asyncio.run(find_intercom_app_id())
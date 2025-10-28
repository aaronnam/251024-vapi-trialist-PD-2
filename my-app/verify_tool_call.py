#!/usr/bin/env python3
"""Verify that the agent's unleash_search_knowledge tool is callable and works."""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import Mock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agent import PandaDocTrialistAgent
from livekit.agents import RunContext


async def test_tool_directly():
    """Test calling the Unleash tool directly."""

    print("\n=== Direct Tool Call Test ===")

    # Create agent instance
    agent = PandaDocTrialistAgent()

    # Create mock context
    mock_context = Mock(spec=RunContext)

    # Test 1: Call tool with valid query
    print("\n1. Testing with 'How do I create templates?'...")
    try:
        result = await agent.unleash_search_knowledge(
            context=mock_context,
            query="How do I create templates?",
            response_format="concise"
        )
        print(f"   ✅ Tool called successfully!")
        print(f"   → Found: {result.get('found', False)}")
        print(f"   → Total results: {result.get('total_results', 0)}")
        if result.get('answer'):
            print(f"   → Answer preview: {result.get('answer')[:100]}...")
    except Exception as e:
        print(f"   ❌ Tool call failed: {e}")

    # Test 2: Call tool with non-PandaDoc query
    print("\n2. Testing with 'quantum computing'...")
    try:
        result = await agent.unleash_search_knowledge(
            context=mock_context,
            query="quantum computing",
            response_format="concise"
        )
        print(f"   ✅ Tool called successfully!")
        print(f"   → Found: {result.get('found', False)}")
        print(f"   → Total results: {result.get('total_results', 0)}")
    except Exception as e:
        print(f"   ❌ Tool call failed: {e}")

    # Check if tool is registered
    print("\n3. Checking tool registration...")
    tools = []
    for attr_name in dir(agent):
        attr = getattr(agent, attr_name)
        if hasattr(attr, '__name__') and 'unleash' in attr.__name__.lower():
            tools.append(attr_name)

    if tools:
        print(f"   ✅ Found tool methods: {tools}")
    else:
        print("   ❌ No unleash tools found in agent")

    print("\n=== Test Complete ===\n")


if __name__ == "__main__":
    # Check environment
    api_key = os.getenv("UNLEASH_API_KEY")
    base_url = os.getenv("UNLEASH_BASE_URL", "https://e-api.unleash.so")
    app_id = os.getenv("UNLEASH_INTERCOM_APP_ID", "intercom")

    print("Environment Check:")
    print(f"  UNLEASH_API_KEY: {'✅ Set' if api_key else '❌ Not set'}")
    print(f"  UNLEASH_BASE_URL: {base_url}")
    print(f"  UNLEASH_INTERCOM_APP_ID: {app_id}")

    # Run test
    asyncio.run(test_tool_directly())
#!/usr/bin/env python3
"""Direct test to verify Unleash tool is being called."""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from livekit.agents import AgentSession, inference
from agent import PandaDocTrialistAgent

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_unleash_tool_call():
    """Test if the agent actually calls the Unleash tool."""

    print("\n=== Testing Unleash Tool Call ===")

    # Create agent
    agent = PandaDocTrialistAgent()

    # Set up session with minimal LLM
    async with (
        inference.LLM(model="openai/gpt-4o-mini") as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(agent)

        # Test 1: PandaDoc question
        print("\nTest 1: Asking about templates...")
        result = await session.run(user_input="How do I create templates?")

        # Check if tool was called
        events = []
        try:
            for _ in range(10):  # Collect up to 10 events
                event = result.expect.next_event()
                events.append(event)
                print(f"  Event: {type(event).__name__}")

                # Check for function call
                if hasattr(event, 'item') and isinstance(event.item, dict):
                    if 'name' in event.item:
                        print(f"  → Tool called: {event.item['name']}")
                        if event.item['name'] == 'unleash_search_knowledge':
                            print("  ✅ UNLEASH TOOL WAS CALLED!")
                            if 'arguments' in event.item:
                                print(f"  → Arguments: {event.item['arguments']}")
        except:
            pass  # No more events

        # Test 2: Non-PandaDoc question
        print("\nTest 2: Asking about quantum computing...")
        result2 = await session.run(user_input="Tell me about quantum computing")

        try:
            event = result2.expect.next_event()
            if hasattr(event, 'item') and isinstance(event.item, dict):
                if 'name' in event.item and event.item['name'] == 'unleash_search_knowledge':
                    print("  ✅ Tool called even for non-PandaDoc topic (good!)")
                else:
                    print(f"  ❌ Different tool called: {event.item.get('name', 'unknown')}")
            else:
                print("  ❌ No tool call detected")
        except:
            print("  ❌ No events received")

    print("\n=== Test Complete ===\n")


if __name__ == "__main__":
    # Check if API key is set
    if not os.getenv("UNLEASH_API_KEY"):
        print("⚠️  Warning: UNLEASH_API_KEY not set in environment")

    # Run the test
    asyncio.run(test_unleash_tool_call())
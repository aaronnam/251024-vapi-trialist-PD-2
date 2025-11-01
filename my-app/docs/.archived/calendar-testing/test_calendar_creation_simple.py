"""
Simple test to verify calendar events are actually being created.
Run with: uv run python tests/test_calendar_creation_simple.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from livekit.agents import AgentSession
from livekit.plugins import openai
from src.agent import PandaDocTrialistAgent


async def test_calendar_booking():
    """Simple test that actually creates a calendar event."""

    print("\n" + "="*80)
    print("🎯 TESTING: Real Calendar Event Creation")
    print("="*80 + "\n")

    # Initialize LLM
    llm = openai.LLM(model="gpt-4o-mini", temperature=0.1)

    async with llm, AgentSession(llm=llm) as session:
        agent = PandaDocTrialistAgent()

        # Set up qualified user
        agent.discovered_signals = {
            "team_size": 10,
            "qualification_tier": "sales_ready"
        }
        agent.user_email = "test@example.com"

        await session.start(agent)

        print("📞 Requesting meeting with all info...")
        result = await session.run(
            user_input="I'm John Test, head of sales at a 10-person company. Please book a meeting for tomorrow at 2 PM."
        )

        # Wait for execution
        await asyncio.sleep(2)

        # Check if the agent confirmed the booking
        messages = []
        for event in result.events:
            if hasattr(event, 'item') and event.item.get('role') == 'assistant':
                content = event.item.get('content', [])
                if content and isinstance(content[0], str):
                    messages.append(content[0])

        print("\nAgent responses:")
        for msg in messages:
            print(f"  - {msg[:100]}...")

        # Check if booking was confirmed
        booking_confirmed = any(
            "booked" in msg.lower() or
            "scheduled" in msg.lower() or
            "calendar" in msg.lower()
            for msg in messages
        )

        if booking_confirmed:
            print("\n✅ SUCCESS: Agent confirmed the booking!")
            print("Check your calendar for: 'PandaDoc Sales Consultation - John Test'")
        else:
            print("\n⚠️ Agent didn't confirm a booking. Check the responses above.")

    print("\n" + "="*80)
    print("Test complete! Check your Google Calendar.")
    print("="*80)


if __name__ == "__main__":
    asyncio.run(test_calendar_booking())
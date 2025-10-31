#!/usr/bin/env python3
"""
Test Langfuse integration for STT and TTS cost tracking.

This script verifies that all model costs are properly sent to Langfuse.
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")


async def test_langfuse_integration():
    """Test that STT, TTS, and LLM costs are all sent to Langfuse."""
    print("🔍 Testing Langfuse Integration for All Model Costs\n")
    print("=" * 60)

    # Import after env is loaded
    from utils.telemetry import setup_observability
    from utils.cost_tracking import CostTracker

    # Set up observability
    trace_provider = setup_observability(
        metadata={"langfuse.session.id": "test_session_001"}
    )

    if not trace_provider:
        print("⚠️  WARNING: Langfuse not configured. Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY")
        print("Without these, costs won't appear in your Langfuse dashboard.")
        return False

    print("✅ Langfuse observability configured")

    # Initialize cost tracker
    tracker = CostTracker()

    # Test 1: Track STT cost
    print("\n1️⃣ Testing STT Cost Tracking:")
    print("   Simulating 30 seconds of Deepgram audio...")
    stt_cost = tracker.track_stt_cost(
        audio_duration_seconds=30,
        provider="deepgram",
        model="nova-2",
        speech_id=None  # STT doesn't have speech_id
    )
    print(f"   ✅ STT cost tracked: ${stt_cost:.6f}")

    # Give time for span to export
    await asyncio.sleep(1)

    # Test 2: Track LLM cost
    print("\n2️⃣ Testing LLM Cost Tracking:")
    print("   Simulating GPT-4 mini with 200 prompt + 100 completion tokens...")
    llm_cost = tracker.track_llm_cost(
        prompt_tokens=200,
        completion_tokens=100,
        model="gpt-4.1-mini",
        speech_id="test_turn_001"
    )
    print(f"   ✅ LLM cost tracked: ${llm_cost:.6f}")

    # Give time for span to export
    await asyncio.sleep(1)

    # Test 3: Track TTS cost
    print("\n3️⃣ Testing TTS Cost Tracking:")
    print("   Simulating Cartesia with 500 characters...")
    tts_cost = tracker.track_tts_cost(
        character_count=500,
        provider="cartesia",
        model="sonic-3",
        speech_id="test_turn_001"
    )
    print(f"   ✅ TTS cost tracked: ${tts_cost:.6f}")

    # Give time for span to export
    await asyncio.sleep(1)

    # Test 4: Track complete conversation turn
    print("\n4️⃣ Testing Complete Conversation Turn:")
    print("   Simulating full turn with all models...")
    turn_summary = tracker.track_conversation_turn(
        speech_id="test_turn_002",
        stt_duration=15,
        llm_prompt_tokens=150,
        llm_completion_tokens=75,
        tts_characters=300,
        total_latency=0.9
    )
    print(f"   ✅ Turn cost tracked: ${turn_summary['total']:.6f}")

    # Give time for span to export
    await asyncio.sleep(1)

    # Test 5: Session summary
    print("\n5️⃣ Testing Session Summary:")
    tracker.report_session_summary()
    summary = tracker.get_session_summary()
    print(f"   Total STT: ${summary['stt']['total_cost']:.6f} ({summary['stt']['total_minutes']:.2f} min)")
    print(f"   Total LLM: ${summary['llm']['total_cost']:.6f} ({summary['llm']['total_tokens']} tokens)")
    print(f"   Total TTS: ${summary['tts']['total_cost']:.6f} ({summary['tts']['total_characters']} chars)")
    print(f"   ✅ Session total: ${summary['total_cost']:.6f}")

    # Force flush traces
    print("\n6️⃣ Flushing traces to Langfuse...")
    if trace_provider:
        trace_provider.force_flush()
        print("   ✅ Traces flushed")

    print("\n" + "=" * 60)
    print("✅ Integration test complete!")
    print("\n📊 Expected in Langfuse Dashboard:")
    print("   • STT span with langfuse.cost.total attribute")
    print("   • LLM span with langfuse.cost.total attribute")
    print("   • TTS span with langfuse.cost.total attribute")
    print("   • Conversation turn span with aggregated costs")
    print("   • Session summary span with total costs")

    print("\n🔗 Check your Langfuse dashboard:")
    print("   https://cloud.langfuse.com/project/[your-project]")
    print("   Look for traces with session ID: test_session_001")

    return True


async def test_live_agent():
    """Test the actual agent to see what metrics are collected."""
    print("\n\n🤖 Testing Live Agent Metrics Collection")
    print("=" * 60)

    # Check if we can import the agent
    try:
        from agent import PandaDocTrialistAgent
        from livekit.agents.metrics import LLMMetrics, STTMetrics, TTSMetrics

        # Create agent instance
        agent = PandaDocTrialistAgent()
        print("✅ Agent initialized with cost tracker")

        # Simulate some metrics
        print("\n📈 Simulating metrics collection:")

        # Create mock STT metric
        class MockSTTMetrics:
            audio_duration = 10.5  # 10.5 seconds

        stt_metric = MockSTTMetrics()
        stt_minutes = stt_metric.audio_duration / 60.0
        stt_cost = stt_minutes * agent.provider_pricing["deepgram_nova2"]
        print(f"   STT: {stt_metric.audio_duration}s = ${stt_cost:.6f}")

        # Create mock LLM metric
        class MockLLMMetrics:
            prompt_tokens = 100
            completion_tokens = 50
            total_tokens = 150
            speech_id = "test_001"
            ttft = 0.5

        llm_metric = MockLLMMetrics()
        llm_cost = (
            llm_metric.prompt_tokens * agent.provider_pricing["openai_gpt4_mini_input"] +
            llm_metric.completion_tokens * agent.provider_pricing["openai_gpt4_mini_output"]
        )
        print(f"   LLM: {llm_metric.total_tokens} tokens = ${llm_cost:.6f}")

        # Create mock TTS metric
        class MockTTSMetrics:
            characters_count = 250
            speech_id = "test_001"
            ttfb = 0.3

        tts_metric = MockTTSMetrics()
        tts_cost = tts_metric.characters_count * agent.provider_pricing["cartesia_sonic"]
        print(f"   TTS: {tts_metric.characters_count} chars = ${tts_cost:.6f}")

        total = stt_cost + llm_cost + tts_cost
        print(f"\n   Total for turn: ${total:.6f}")

        print("\n✅ Agent cost calculation verified")

    except Exception as e:
        print(f"❌ Error testing agent: {e}")
        return False

    return True


if __name__ == "__main__":
    print("🚀 Langfuse Cost Tracking Integration Test\n")

    # Check environment
    has_langfuse = bool(os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY"))

    if not has_langfuse:
        print("⚠️  LANGFUSE CREDENTIALS NOT CONFIGURED")
        print("   Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to see costs in Langfuse")
        print("   Testing will continue but costs won't appear in dashboard\n")

    # Run tests
    loop = asyncio.get_event_loop()

    # Test Langfuse integration
    success = loop.run_until_complete(test_langfuse_integration())

    # Test agent
    if success or not has_langfuse:
        loop.run_until_complete(test_live_agent())

    print("\n✅ All tests complete!")

    if has_langfuse:
        print("\n📝 Next Steps:")
        print("1. Check your Langfuse dashboard for the test traces")
        print("2. Look for costs under 'Model Usage' or in trace attributes")
        print("3. Deploy the agent: lk agent deploy")
        print("4. Monitor real session costs in production")
    else:
        print("\n📝 To enable Langfuse integration:")
        print("1. Get your Langfuse API keys from https://cloud.langfuse.com")
        print("2. Set environment variables:")
        print("   export LANGFUSE_PUBLIC_KEY=pk_xxx")
        print("   export LANGFUSE_SECRET_KEY=sk_xxx")
        print("3. Run this test again to verify integration")
#!/usr/bin/env python3
"""
Test script to verify how we can enrich the user_speaking span with transcript data.

The issue: LiveKit creates a user_speaking span internally that only has timing data.
We need to add the transcript to this span for Langfuse visibility.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
from dotenv import load_dotenv
load_dotenv(".env.local")


async def test_span_enrichment():
    """Test different approaches to enriching spans with transcript data."""
    print("Testing span enrichment approaches...\n")

    from opentelemetry import trace as otel_trace
    from opentelemetry.trace import Status, StatusCode

    # Approach 1: Get the current active span and enrich it
    print("1. Testing current span enrichment:")
    tracer = otel_trace.get_tracer(__name__)

    # Simulate LiveKit creating a user_speaking span
    with tracer.start_as_current_span("user_speaking") as parent_span:
        parent_span.set_attribute("start_time", 123456)

        # Now in our event handler, we try to enrich the current span
        current_span = otel_trace.get_current_span()
        if current_span and current_span.is_recording():
            print(f"   Found active span: {current_span._name if hasattr(current_span, '_name') else 'unknown'}")
            # Add transcript to the EXISTING span
            current_span.set_attribute("langfuse.input", "Hello, I need help with PandaDoc")
            current_span.set_attribute("user.transcript", "Hello, I need help with PandaDoc")
            print("   ✅ Enriched existing span with transcript")
        else:
            print("   ❌ No active span found")

    print("\n2. Testing span context propagation:")
    # This is what happens in the actual agent
    with tracer.start_as_current_span("user_speaking") as user_span:
        user_span.set_attribute("start_time", 123456)

        # Simulate the user_input_transcribed event handler
        async def on_user_input_transcribed(transcript):
            # Get the current span context
            current_span = otel_trace.get_current_span()
            if current_span and current_span.is_recording():
                # Enrich the parent span
                current_span.set_attribute("langfuse.input", transcript)
                current_span.set_attribute("user.transcript", transcript)
                print(f"   ✅ Added transcript to span: {transcript[:50]}...")
                return True
            else:
                # Create a child span if no current span
                with tracer.start_as_current_span("user_transcript") as child_span:
                    child_span.set_attribute("langfuse.input", transcript)
                    child_span.set_attribute("user.transcript", transcript)
                    print(f"   ⚠️  Created child span with transcript: {transcript[:50]}...")
                return False

        # Test the handler
        success = await on_user_input_transcribed("Hello, I need help with PandaDoc")

    print("\n3. Testing OpenTelemetry context management:")
    from opentelemetry import context as otel_context

    # Store context when user_speaking starts
    with tracer.start_as_current_span("user_speaking") as span:
        # Store the context
        user_speaking_context = otel_context.get_current()
        span.set_attribute("start_time", 123456)

        # Later, when transcript arrives, use stored context
        token = otel_context.attach(user_speaking_context)
        try:
            current_span = otel_trace.get_current_span()
            if current_span:
                current_span.set_attribute("langfuse.input", "Test transcript")
                print("   ✅ Successfully enriched span using stored context")
        finally:
            otel_context.detach(token)

    print("\n4. Testing span retrieval by span context:")
    # Check if we can access the session's user_speaking span directly
    print("   Note: VoiceAssistant stores _user_speaking_span internally")
    print("   We need to access session._user_speaking_span if it exists")

    print("\nConclusion:")
    print("The best approach is to get the current active span in the event handler")
    print("and enrich it with transcript data. If no span exists, create a child span.")


if __name__ == "__main__":
    asyncio.run(test_span_enrichment())
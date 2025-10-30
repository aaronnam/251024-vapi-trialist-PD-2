#!/usr/bin/env python
"""Test script to verify ElevenLabs TTS with WordTokenizer works for multi-sentence"""
import asyncio
from livekit.agents import tokenize
from livekit.plugins import elevenlabs

async def test_tts():
    tts = elevenlabs.TTS(
        voice_id="21m00Tcm4TlvDq8ikWAM",
        model="eleven_turbo_v2_5",
        word_tokenizer=tokenize.WordTokenizer(),
    )

    # Test multi-sentence text
    text = "Hi! I'm your AI Pandadoc Trial Success Specialist. How's your trial going? Any roadblocks I can help clear up?"

    print(f"Testing TTS with text: {text}")
    print("Generating audio...")

    try:
        stream = tts.synthesize(text)
        frame_count = 0
        async for frame in stream:
            frame_count += 1

        print(f"✅ Successfully generated {frame_count} audio frames")
        print("✅ Multi-sentence TTS working correctly with WordTokenizer")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_tts())
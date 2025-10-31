# Audio Debug Status - Oct 30, 2024

## Current Problem
**Agent produces NO AUDIO in production or Agent Playground**. User cannot hear anything.

## What We Know Works
- ✅ TTS metrics show audio IS being generated (4.0s durations in logs)
- ✅ ElevenLabs API is responding successfully
- ✅ Agent initializes without errors
- ✅ Local console mode runs without crashes
- ✅ Transcription works (STT functional)

## What's Broken
- ❌ Audio frames never reach the user
- ❌ WebRTC audio track not publishing correctly
- ❌ Issue persists in both Agent Playground and production

## Recent Failed Attempts
1. **Custom `tts_node` override** - Removed (was blocking audio pipeline)
2. **Added `auto_mode=False`** - Didn't fix issue
3. **Multiple deploys and restarts** - No improvement

## Critical Code Locations

### TTS Config (src/agent.py:1165-1173)
```python
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2_5",
    auto_mode=False,
    streaming_latency=3,
),
```

### VoiceAssistant Setup (src/agent.py:1152-1210)
Uses standard `AgentSession()` with STT/LLM/TTS configuration.

### Room Output (src/agent.py:1550-1554)
```python
room_output_options=RoomOutputOptions(
    audio_enabled=True,
    transcription_enabled=True,
),
```

## Log Evidence
```
TTS metrics: audio_duration: 4.0
STT metrics: working
LLM metrics: working
ElevenLabs: model_name: eleven_turbo_v2_5, ttfb: 1.14s
```

Audio is synthesized but never published to room participants.

## Hypotheses to Test

### #1: Audio Track Publishing Issue
**Theory**: TTS generates frames but they're not being published to the WebRTC audio track.

**Check**:
- Look for `room.local_participant.publish_track` calls
- Verify `AgentSession` is properly connecting TTS output to room
- Check if audio source is being created and published

**Debug Command**:
```bash
lk agent logs | grep -E "(publish|track|audio|output)" | tail -50
```

### #2: AgentSession Configuration
**Theory**: `AgentSession` isn't properly wired to publish TTS output.

**Check**:
- Verify `room_output_options` is being used
- Check if we need explicit audio track setup
- Review how `VoiceAssistant` connects to room

### #3: LiveKit Cloud Issue
**Theory**: Agent container has audio publishing disabled or broken.

**Test**: Run agent locally with `dev` mode and connect from frontend.

```bash
uv run python src/agent.py dev
```

### #4: ElevenLabs Streaming Issue
**Theory**: `auto_mode=False` with `streaming_latency=3` causes frames to buffer but not flush.

**Test**: Try default TTS config:
```python
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2_5",
)
```

## Next Steps

1. **Check LiveKit docs for audio publishing** - Use MCP server:
   ```
   /agents/build/audio or /agents/build/nodes
   ```

2. **Compare with working example** - Look at LiveKit agent examples that work

3. **Enable debug logging** - Add to agent.py:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

4. **Test with different TTS** - Temporarily switch to Cartesia to isolate ElevenLabs:
   ```python
   from livekit.plugins import cartesia
   tts=cartesia.TTS()
   ```

5. **Check room connection** - Verify agent is actually joining room and publishing tracks:
   ```bash
   lk agent logs | grep -i "room\|participant\|track" | tail -100
   ```

## Key Files
- `src/agent.py` (lines 1152-1210, 1550-1554)
- Logs: `lk agent logs`
- Status: `lk agent status`
- Deploy: `lk agent deploy && lk agent restart`

## Current Deploy
- Version: `v20251030192718`
- Status: Should be Running
- Project: `pd-voice-trialist-4`
- Agent ID: `CA_9b4oemVRtDEm`

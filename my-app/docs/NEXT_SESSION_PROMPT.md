# Audio Publishing Debug - Session Handoff

## Problem Statement
LiveKit voice agent generates TTS audio successfully (confirmed by metrics showing 4.0s audio durations) but users hear NOTHING in Agent Playground or production. Audio frames are not reaching WebRTC tracks.

## Your Mission
Debug and fix the audio track publishing issue. TTS works, room connection works, but audio output fails silently.

## Critical Context Files
1. Read `docs/AUDIO_DEBUG_STATUS.md` - Full problem context
2. Check `src/agent.py` lines 1152-1210 (VoiceAssistant setup)
3. Check `src/agent.py` lines 1550-1554 (RoomOutputOptions)

## Start Here

### Step 1: Verify Current State
```bash
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app
lk agent status
lk agent logs | grep -E "(publish|track|audio)" | tail -30
```

### Step 2: Use LiveKit Docs MCP
Query the MCP server to understand audio publishing:
- Search for "audio output" and "publishing tracks"
- Look at `/agents/build/audio` and `/agents/build/nodes`
- Find working examples of AgentSession audio output

### Step 3: Compare With Working Example
Find a minimal working LiveKit agent example and compare:
- How does their `AgentSession` differ?
- Are we missing any required configuration?
- Do they manually publish audio tracks?

### Step 4: Test Hypotheses (Priority Order)

**A. Switch TTS Provider (Quick Test)**
Replace ElevenLabs with Cartesia to isolate the issue:
```python
from livekit.plugins import cartesia
tts=cartesia.TTS()
```
If this works → ElevenLabs config issue. If not → deeper problem.

**B. Enable Debug Logging**
Add to top of src/agent.py:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```
Look for track publishing failures in logs.

**C. Check Room Participant State**
```bash
lk agent logs | grep -i "participant.*publish" | tail -50
```
Verify agent is actually publishing audio tracks to room.

**D. Test Local Dev Mode**
```bash
uv run python src/agent.py dev
```
Connect frontend and test if audio works locally vs cloud.

## Key Diagnostic Commands
```bash
# Watch live logs for audio issues
lk agent logs | grep -E "(audio|track|publish|TTS|frame)"

# Check if tracks are being created
lk agent logs | grep -i "LocalAudioTrack"

# Monitor for WebRTC errors
lk agent logs | grep -i "webrtc\|error\|failed"
```

## Known Good State
- Current version: `v20251030192718`
- TTS generates audio: ✅ (4.0s durations in logs)
- STT/LLM working: ✅
- Agent initializes: ✅
- Audio reaches users: ❌ **THIS IS THE BUG**

## Quick Wins to Try
1. Remove ALL TTS customization, use pure defaults
2. Test with Cartesia TTS instead of ElevenLabs
3. Check if `room_output_options` is actually being used
4. Verify `AgentSession` is the right API (not deprecated)

## Deployment Flow
After any fix:
```bash
git add src/agent.py
git commit -m "Fix: <description>"
lk agent deploy
lk agent restart
# Wait 30s
lk agent status
# Test in Agent Playground
```

## Success Criteria
User hears the full greeting in Agent Playground:
> "Hi! I'm your AI Pandadoc Trial Success Specialist. How's your trial going? Any roadblocks I can help clear up?"

## Important Notes
- Don't over-engineer. Find the simplest working config.
- Console mode (`console` command) works differently than production
- Metrics showing audio duration ≠ audio being published
- This is likely a 1-2 line config issue, not complex code

Start by using the LiveKit docs MCP server to understand the correct audio output pattern.

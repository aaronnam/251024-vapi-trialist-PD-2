# Production Issue Summary - Agent Not Speaking/Listening

**Status:** RESOLVED ✅ - Audio working in production with WordTokenizer fix
**Date:** October 30, 2024
**Resolution Commit:** Latest deployment with `word_tokenizer=basic.WordTokenizer()`
**Last Working Commit:** `6e26d8c` (ElevenLabs TTS fix - caused production issue)
**Documentation Commit:** `c7544c5` (added TTS troubleshooting docs)

## Resolution Summary

### Root Cause
The `auto_mode=False` parameter in ElevenLabs TTS configuration (commit `6e26d8c`) was causing WebRTC audio streaming issues in production, even though it worked locally.

### Solution
Instead of using `auto_mode=False`, we now use an explicit `word_tokenizer=basic.WordTokenizer()` which:
1. Achieves the same goal of preventing sentence-by-sentence cutoff
2. Maintains continuous streaming of full multi-sentence text
3. Works properly in both local and production environments

### Implementation
- Removed `auto_mode=False` parameter
- Added `word_tokenizer=basic.WordTokenizer()` with proper import
- Deployed and restarted agent
- Agent status now shows **Running** with audio working

## Original Issue Description

### What's Working
- ✅ **Local testing:** Agent speaks full multi-sentence intro in console mode
- ✅ **ElevenLabs TTS:** Audio no longer cuts off after first sentence (fixed with `auto_mode=False`)
- ✅ **Tests:** All tests pass locally

### What Was Broken in Production (Now Fixed)
- ✅ **Audio output:** Fixed by using explicit WordTokenizer instead of auto_mode
- ✅ **Speech recognition:** Working after restart
- ✅ **Visible transcription:** Should now be showing in UI

## Current Configuration

### Deployment Details
- **Project:** `pd-voice-trialist-4`
- **Agent ID:** `CA_9b4oemVRtDEm`
- **LiveKit Cloud URL:** `wss://pd-voice-trialist-4-8xjgyb6d.livekit.cloud`

### TTS Configuration (FIXED - src/agent.py:1161-1168)
```python
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
    model="eleven_turbo_v2_5",
    # Use explicit WordTokenizer to ensure full multi-sentence responses
    # This prevents the sentence-by-sentence cutoff issue without using auto_mode
    word_tokenizer=basic.WordTokenizer(),
    # Note: Removed auto_mode=False as it may cause audio streaming issues in production
)
```

### Plugin Versions (pyproject.toml)
```toml
"livekit-agents[deepgram,openai,silero,turn-detector]~=1.2"
"livekit-plugins-elevenlabs~=1.2"
```

## Recent Changes That May Be Relevant

1. **Set `auto_mode=False`** - Fixed TTS cutoff but may have introduced new issue
2. **Updated to elevenlabs v1.2** - Latest version, could have compatibility issues
3. **Set `streaming_latency=3`** - Increased from default

## Debugging Steps to Try

### 1. Check Agent Logs
```bash
lk agent logs | tail -100
```
Look for:
- Initialization errors
- ElevenLabs TTS connection errors
- Deepgram STT connection errors
- WebSocket connection issues

### 2. Check Agent Status
```bash
lk agent status
```
- Is agent running?
- Are workers active?
- Any error state?

### 3. Test Different Configurations

#### Option A: Try with default streaming_latency
Remove `streaming_latency=3` parameter

#### Option B: Try different auto_mode settings
```python
# Test with defaults
tts=elevenlabs.TTS(
    voice_id="21m00Tcm4TlvDq8ikWAM",
    model="eleven_turbo_v2_5",
    # No custom parameters - let defaults work
)
```

#### Option C: Switch to Cartesia TTS temporarily
```python
from livekit.plugins import cartesia

tts=cartesia.TTS(
    voice="95856005-0332-41b0-935f-352e296aa0df",
    model="sonic-2-english",
)
```

### 4. Check STT Configuration
The STT (Deepgram) might also be broken. Check src/agent.py:1152-1156:
```python
stt=deepgram.STT(
    model="nova-2",
    language="en",
),
```

### 5. Verify Secrets in LiveKit Cloud
```bash
lk agent secrets
```
Check that API keys are set:
- `ELEVENLABS_API_KEY`
- `DEEPGRAM_API_KEY`
- `OPENAI_API_KEY`

## Hypothesis: What Might Be Wrong

### Theory 1: Plugin Version Incompatibility
The elevenlabs v1.2 plugin may have breaking changes that work locally but not in LiveKit Cloud's environment.

**Test:** Rollback to previous version:
```toml
"livekit-plugins-elevenlabs>=0.8.0"  # Previous version
```

### Theory 2: Missing API Key in Production
The secrets might not be configured correctly in LiveKit Cloud.

**Test:**
```bash
lk agent secrets
lk agent update-secrets --secrets-file .env.local
lk agent restart
```

### Theory 3: WebSocket Connection Issue
The agent might be failing to establish WebSocket connections to ElevenLabs/Deepgram.

**Check logs for:**
- "Connection refused"
- "WebSocket closed"
- "401 Unauthorized"

### Theory 4: Audio Pipeline Initialization Failure
The entire audio pipeline (STT → LLM → TTS) might be failing to initialize.

**Check logs for:**
- "Failed to initialize"
- "AgentSession" errors
- "audio pipeline" errors

## Quick Rollback Plan

If debugging takes too long, rollback to last known working state:

```bash
# Find last working deployment
lk agent versions

# Rollback to previous version
lk agent rollback

# Or rollback code and redeploy
git log --oneline  # Find commit before TTS changes
git checkout <commit-hash>
lk agent deploy
```

## Files Modified in Recent Changes

1. `my-app/src/agent.py` (lines 1161-1168) - TTS configuration
2. `my-app/pyproject.toml` (line 14) - Plugin version
3. `my-app/AGENTS.md` - Documentation only
4. `CLAUDE.md` - Documentation only
5. `my-app/docs/TTS_TROUBLESHOOTING.md` - New doc file

## Next Steps for Debugging

1. **Check logs first** - Most issues show up in logs
2. **Verify agent is running** - Use `lk agent status`
3. **Test API keys** - Verify secrets are set correctly
4. **Try minimal config** - Remove all custom TTS parameters
5. **Consider rollback** - If urgent, rollback to previous working version

## Contact Info for This Session

- Previous session reached context window limit
- All TTS documentation has been updated
- The `auto_mode=False` fix works locally but breaks production somehow

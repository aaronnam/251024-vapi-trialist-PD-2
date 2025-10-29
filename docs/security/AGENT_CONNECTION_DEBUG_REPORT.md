# Agent Connection Failure - Root Cause Analysis & Fix

**Status**: ✅ **ELEVEN_API_KEY Issue RESOLVED** → ⚠️ **New Issue Found**
**Last Updated**: 2025-10-29 18:52 UTC

## Issue Summary

Users entering their email and pressing "Start Trial" are redirected to the next page, but the voice agent never joins the room. The user sees a stuck "connecting..." state indefinitely.

## Root Cause #1: ELEVEN_API_KEY Missing ✅ RESOLVED

**The LiveKit agent was crashing on startup due to a missing `ELEVEN_API_KEY` environment variable.**

Error from agent logs (2025-10-29 18:12:57):
```
ValueError: ElevenLabs API key is required, either as argument or set ELEVEN_API_KEY environmental variable
```

**Location**: `agent.py` line 1117 - ElevenLabs TTS initialization

**Resolution**: Added `ELEVEN_API_KEY` secret to LiveKit Cloud at 18:44:04. Agent redeployed at 18:50:23. This issue is now fixed.

---

## Root Cause #2: Async Event Handler Error ⚠️ NEW BLOCKER

After resolving the API key issue, a **new error prevents the agent from completing initialization**:

Error from agent logs (2025-10-29 18:50:51):
```
ValueError: Cannot register an async callback with `.on()`.
Use `asyncio.create_task` within your synchronous callback instead.
```

**Location**: `agent.py` line 1289 - Event handler registration

```python
@session.on("user_state_changed")  # ← Line 1289
```

The agent process starts successfully but crashes when trying to register the `user_state_changed` event handler. This prevents the agent from joining the room.

## Evidence

```
{"message": "received job request", "job_id": "AJ_hzf3cu8vBY5K", "room_name": "pandadoc_trial_1761761577101_u9xjyh"}
{"message": "unhandled exception while running the job task", "error": "ValueError: ElevenLabs API key is required..."}
```

A room is created (`pandadoc_trial_1761761577101_u9xjyh`), but the agent never joins because it crashes during initialization.

---

## Solution for Root Cause #2: Async Event Handler

The LiveKit Agents framework changed how event handlers work. The `.on()` method now only accepts **synchronous** callbacks, not async ones.

### **Fix: Wrap async logic in a sync callback**

**Change at `agent.py` line ~1289:**

**OLD (Broken):**
```python
@session.on("user_state_changed")
async def on_user_state_changed(state: dict):
    # async code here
    await some_async_function()
```

**NEW (Fixed):**
```python
@session.on("user_state_changed")
def on_user_state_changed(state: dict):
    asyncio.create_task(handle_user_state_changed(state))

async def handle_user_state_changed(state: dict):
    # async code here
    await some_async_function()
```

**Key changes:**
1. Make the `.on()` callback **synchronous** (remove `async`)
2. Use `asyncio.create_task()` to schedule the async work
3. Move async logic to a separate async function

This pattern applies to **all event handlers** using `.on()`. Check for similar patterns throughout the agent code.

---

## Solution for Root Cause #1: ELEVEN_API_KEY ✅ ALREADY FIXED

### **Option A: Set ELEVEN_API_KEY Secret** ✅ COMPLETED

The API key was added to LiveKit Cloud at 18:44:04 and the agent was redeployed at 18:50:23. This issue is now resolved.

---

### **Alternative: Switch to OpenAI TTS (Optional)**

If you want to avoid ElevenLabs dependency entirely, replace with OpenAI TTS. OpenAI API key is already configured and used for the LLM, so **no additional credentials needed**.

**Code changes in `agent.py`:**

1. **Line ~29** - Update import:
   ```python
   # OLD
   from livekit.plugins import deepgram, elevenlabs, noise_cancellation, openai, silero

   # NEW
   from livekit.plugins import deepgram, noise_cancellation, openai, silero
   ```

2. **Lines ~1117-1120** - Replace TTS initialization:
   ```python
   # OLD
   tts=elevenlabs.TTS(
       voice="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
       model="eleven_turbo_v2_5",
   ),

   # NEW
   tts=openai.TTS(
       model="tts-1",    # Fast model for real-time
       voice="nova",     # Natural female voice
   ),
   ```

**Voice options**: `alloy`, `echo`, `fable`, `onyx`, `shimmer` (male), or `nova`, `coral` (female)

**Pros**:
- No new API keys needed
- Higher quality TTS
- Better integration with existing OpenAI LLM
- Eliminates dependency on ElevenLabs

**Cons**: Voice characteristics will change slightly

---

## Testing the Fix

After fixing the async event handler issue:

1. **Fix the event handler** at line 1289 in `agent.py` (see solution above)

2. **Redeploy the agent**:
   ```bash
   cd <path-to-agent>
   lk agent deploy --project pd-voice-trialist-4 .
   ```

3. **Verify agent is running**:
   ```bash
   lk agent logs --id CA_9b4oemVRtDEm
   ```
   Should show:
   - ✅ `registered worker`
   - ✅ `received job request`
   - ✅ No `ValueError` exceptions
   - ✅ Agent joins the room successfully

4. **Test the flow**:
   - User enters email → clicks "Start Trial"
   - Should see agent join within 2-3 seconds
   - Room should show 2 participants (user + agent)
   - Voice visualizer shows agent is listening

5. **Verify room has 2 participants**:
   ```bash
   lk room list
   lk room participants list <room_name>
   ```
   Should show both the user and the agent participant.

---

## Priority Actions

1. **Immediate**: Fix the async event handler error at line 1289 (blocks agent from joining)
2. **Already Done**: ELEVEN_API_KEY secret is set and working ✅
3. **Optional**: Consider switching to OpenAI TTS to simplify dependencies

---

**Report Date**: 2025-10-29
**Agent ID**: `CA_9b4oemVRtDEm`
**Project**: `pd-voice-trialist-4`

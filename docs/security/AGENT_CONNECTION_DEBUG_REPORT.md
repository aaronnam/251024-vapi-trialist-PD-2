# Agent Connection Failure - Root Cause Analysis & Fix

**Status**: ✅ **ELEVEN_API_KEY Issue RESOLVED** → ✅ **Async Event Handler FIXED**
**Last Updated**: 2025-10-29 19:03 UTC

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

## Root Cause #2: Async Event Handler Error ✅ FIXED

After resolving the API key issue, a **previous error was preventing the agent from completing initialization**:

Error from agent logs (2025-10-29 18:50:51):
```
ValueError: Cannot register an async callback with `.on()`.
Use `asyncio.create_task` within your synchronous callback instead.
```

**Location**: `agent.py` line 1289 - Event handler registration (NOW FIXED)

**RESOLUTION**: Fixed on 2025-10-29 19:03 UTC by restructuring the event handler:
- Removed `async` from the `@session.on()` callback
- Created a separate async function `handle_user_state_changed()` for the async logic
- The callback now uses `asyncio.create_task()` to schedule the async work
- Agent redeployed with version v20251029185847 - running successfully

## Evidence

```
{"message": "received job request", "job_id": "AJ_hzf3cu8vBY5K", "room_name": "pandadoc_trial_1761761577101_u9xjyh"}
{"message": "unhandled exception while running the job task", "error": "ValueError: ElevenLabs API key is required..."}
```

A room is created (`pandadoc_trial_1761761577101_u9xjyh`), but the agent never joins because it crashes during initialization.

---

## Solution for Root Cause #2: Async Event Handler ✅ IMPLEMENTED

The LiveKit Agents framework requires synchronous callbacks for `.on()` event handlers. Async functions cannot be directly registered.

### **Fix Applied: Wrapped async logic in synchronous callback**

**Changed at `agent.py` lines 1289-1320:**

**OLD (Broken):**
```python
@session.on("user_state_changed")
async def on_user_state_changed(state: dict):
    # async code here
    await some_async_function()
```

**NEW (Fixed - DEPLOYED):**
```python
async def handle_user_state_changed(state: dict):
    # async code here
    await some_async_function()

@session.on("user_state_changed")
def on_user_state_changed(state: dict):
    asyncio.create_task(handle_user_state_changed(state))
```

**Key changes implemented:**
1. ✅ Made the `.on()` callback **synchronous** (removed `async`)
2. ✅ Used `asyncio.create_task()` to schedule the async work
3. ✅ Moved async logic to separate async function
4. ✅ Verified no other async event handlers exist in code

**Deployment Status:**
- ✅ Code fixed and deployed to LiveKit Cloud (version v20251029185847)
- ✅ Agent running successfully
- ✅ No more async handler errors in logs

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

1. **✅ COMPLETED**: Fixed async event handler error at lines 1289-1320 (agent now joins successfully)
2. **✅ ALREADY DONE**: ELEVEN_API_KEY secret is set and working ✅
3. **OPTIONAL**: Consider switching to OpenAI TTS to simplify dependencies

---

**Report Date**: 2025-10-29
**Agent ID**: `CA_9b4oemVRtDEm`
**Project**: `pd-voice-trialist-4`

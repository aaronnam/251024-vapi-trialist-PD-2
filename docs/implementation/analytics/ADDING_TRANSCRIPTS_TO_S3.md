# Adding Transcripts to S3 Analytics Export

**Status**: Currently transcripts are NOT exported to S3
**Goal**: Include full conversation transcripts in session analytics data

---

## Options Comparison

| Option | Complexity | Latency Impact | Completeness | Recommended |
|--------|-----------|----------------|--------------|-------------|
| **1. Use session.history** | Low | None | ✅ Complete | ✅ **Best** |
| **2. Manual collection** | Medium | None | ⚠️ Partial | Only if #1 fails |
| **3. Post-processing** | High | N/A | ✅ Complete | If async OK |

---

## Option 1: Use LiveKit's `session.history` (Recommended)

LiveKit maintains the complete conversation history in `session.history`. Access it at shutdown.

### Implementation

Modify `my-app/src/agent.py` in the `export_session_data()` function:

```python
async def export_session_data():
    """Export session data to analytics queue on shutdown."""
    limit_checker.cancel()

    try:
        usage_summary = agent.usage_collector.get_summary()

        # NEW: Extract transcript from session history
        transcript = []
        if hasattr(session, 'history'):
            for msg in session.history:
                # Each message has: role, content, timestamp
                transcript.append({
                    "role": msg.role,  # "user" or "assistant"
                    "content": msg.content,
                    "timestamp": msg.timestamp if hasattr(msg, 'timestamp') else None
                })

        session_payload = {
            # Existing fields...
            "session_id": ctx.room.name,
            "user_email": agent.session_data.get("user_email", ""),
            # ... all other existing fields ...

            # NEW: Add transcript
            "transcript": transcript,  # Full conversation history
            "transcript_text": "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in transcript
            ]),  # Plain text version for easy reading
        }

        await send_to_analytics_queue(session_payload)
```

### Pros
- ✅ Zero latency impact (collected by LiveKit automatically)
- ✅ Complete conversation history
- ✅ Minimal code changes (~10 lines)
- ✅ Includes timestamps

### Cons
- ⚠️ Need to verify session.history structure (might need LiveKit docs check)

### File Size Impact
- Current: ~300 bytes compressed
- With transcript (10 min call, ~2000 words): ~2-3 KB compressed
- Still very small, negligible cost increase

---

## Option 2: Manual Collection During Session

If `session.history` doesn't work, collect messages manually.

### Implementation

```python
# In entrypoint() function, add message tracking
conversation_messages = []

# After agent creation, add message listeners
@agent.on("agent_speech_committed")
def on_agent_speech(message):
    conversation_messages.append({
        "role": "assistant",
        "content": message.content,
        "timestamp": datetime.now().isoformat()
    })

@agent.on("user_speech_committed")
def on_user_speech(message):
    conversation_messages.append({
        "role": "user",
        "content": message.content,
        "timestamp": datetime.now().isoformat()
    })

# In export_session_data()
session_payload = {
    # ... existing fields ...
    "transcript": conversation_messages,
}
```

### Pros
- ✅ Full control over what's captured
- ✅ Can add custom metadata per message

### Cons
- ⚠️ More code to maintain
- ⚠️ Might miss some edge cases
- ⚠️ Need to verify event names with LiveKit SDK

---

## Option 3: Post-Processing via LiveKit API

Fetch transcripts after the call via LiveKit's API.

### Implementation

Separate script that runs periodically:

```python
import livekit.api
import boto3
import json

async def fetch_and_merge_transcripts():
    """Fetch transcripts from LiveKit and merge with S3 analytics."""

    lk_api = livekit.api.LiveKitAPI(
        url=os.getenv('LIVEKIT_URL'),
        api_key=os.getenv('LIVEKIT_API_KEY'),
        api_secret=os.getenv('LIVEKIT_API_SECRET')
    )

    s3 = boto3.client('s3')

    # List recent sessions from S3
    for session_file in s3.list_objects(...):
        session_id = extract_session_id(session_file)

        # Fetch transcript from LiveKit
        transcript = await lk_api.get_room_transcript(room_name=session_id)

        # Download session data, add transcript, re-upload
        # ...
```

### Pros
- ✅ Doesn't impact agent performance at all
- ✅ Can be run as batch job

### Cons
- ❌ More complex infrastructure
- ❌ Transcript available later (not immediately)
- ❌ Need to check if LiveKit stores transcripts (might not)

---

## Recommended Approach: Option 1 + Verification

**Step 1**: Test if `session.history` exists and has the data we need

Add this to your test script:

```python
# In my-app/src/agent.py, in export_session_data()
# Add temporary logging to see what's available:

logger.info(f"Session attributes: {dir(session)}")
if hasattr(session, 'history'):
    logger.info(f"History available with {len(session.history)} messages")
    logger.info(f"Sample message: {session.history[0] if session.history else 'empty'}")
```

**Step 2**: Make a test call and check logs

```bash
lk agent logs | grep -A 10 "Session attributes"
```

**Step 3**: Based on what we find, implement the appropriate option

---

## My Recommendation

Start with **Option 1** (session.history) because:
1. It's the cleanest implementation (10 lines of code)
2. Zero performance impact
3. LiveKit already maintains this for the LLM context
4. If it doesn't work, fall back to Option 2

Would you like me to:
1. **Implement Option 1** and test it with a quick verification?
2. **Check LiveKit docs first** to confirm session.history structure?
3. **Try all options** and benchmark which works best?

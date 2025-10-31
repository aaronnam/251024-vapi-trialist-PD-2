# Transcript Capture Issue - Diagnosis & Fix

**Date**: October 31, 2025
**Issue**: Transcripts are empty in S3 exports - `transcript: []` and `transcript_text: ""`
**Symptom**: User speaking is not being logged in Langfuse or captured in S3

---

## 🔍 Root Cause Analysis

Based on the documentation and your code review, here are the likely causes:

### 1. **session.history is Empty at Shutdown**

Your code correctly tries to extract from `session.history`, but this might be empty if:

- **Consent not obtained** - Your agent requires consent before proceeding
- **Conversation stuck in GREETING state** - No messages added to history yet
- **History not populated** - `AgentSession` might not be adding messages to history

### 2. **ChatContext Iteration Issue**

According to LiveKit Agents 1.0 documentation:
- `ChatContext` contains `ChatMessage`, `FunctionCall`, and `FunctionCallOutput` items
- Each `ChatMessage` has a `role` and a list of `content` items
- Content items can be `TextContent`, `ImageContent`, or `AudioContent`

Your current code looks correct, but there might be a type filtering issue.

### 3. **Timing Issue**

The transcript extraction happens in `export_session_data()` which is a shutdown callback. If the session ends abruptly or before messages are committed, the history might be empty.

---

## 🛠️ Recommended Fixes

### Fix 1: Add Diagnostic Logging (Immediate)

First, let's add logging to see what's actually in `session.history`:

```python
# In export_session_data() function, around line 1533
try:
    if hasattr(session, 'history') and session.history:
        # ADD DIAGNOSTIC LOGGING
        logger.info(f"🔍 session.history exists: {session.history is not None}")

        # Try to get all items
        chat_messages = list(session.history)
        logger.info(f"🔍 Number of items in history: {len(chat_messages)}")

        # Log each item type
        for i, msg in enumerate(chat_messages):
            logger.info(f"🔍 Item {i}: type={type(msg).__name__}, role={getattr(msg, 'role', 'N/A')}")
            if hasattr(msg, 'content'):
                logger.info(f"   Content type: {type(msg.content)}, items: {len(msg.content) if isinstance(msg.content, list) else 'not a list'}")

        # Rest of your existing code...
        for msg in chat_messages:
            # ... existing extraction logic
```

This will help us see:
1. Is `session.history` populated?
2. How many items are there?
3. What types are they?
4. Do they have content?

### Fix 2: Filter for ChatMessage Type Only

The documentation shows that `ChatContext` can contain different item types. We should filter for `ChatMessage` specifically:

```python
from livekit.agents import llm

# In export_session_data()
try:
    if hasattr(session, 'history') and session.history:
        all_items = list(session.history)
        logger.info(f"Total items in history: {len(all_items)}")

        # Filter for ChatMessage items only
        chat_messages = [
            item for item in all_items
            if isinstance(item, llm.ChatMessage)
        ]
        logger.info(f"ChatMessage items: {len(chat_messages)}")

        for msg in chat_messages:
            role = msg.role  # Should be 'user' or 'assistant'

            # Extract text from content items
            content_text = ""
            for content_item in msg.content:
                # Check if it's TextContent
                if hasattr(content_item, 'text'):
                    content_text += content_item.text

            if content_text.strip():
                transcript.append({
                    "role": role,
                    "content": content_text,
                })
                transcript_text += f"{role.upper()}: {content_text}\n"

        logger.info(f"✅ Extracted {len(transcript)} transcript messages")

except Exception as e:
    logger.error(f"❌ Transcript extraction failed: {e}", exc_info=True)
```

### Fix 3: Use conversation_item_added Event (Alternative Approach)

Instead of relying on `session.history` at shutdown, capture messages as they happen:

```python
# In your entrypoint() function, after session.start()

# Real-time transcript collection
conversation_transcript = []

@session.on("conversation_item_added")
def on_conversation_item(item):
    """Capture conversation items in real-time"""
    try:
        from livekit.agents import llm

        # Only process ChatMessage items
        if isinstance(item, llm.ChatMessage):
            # Extract text content
            content_text = ""
            for content_item in item.content:
                if hasattr(content_item, 'text'):
                    content_text += content_item.text

            if content_text.strip():
                conversation_transcript.append({
                    "role": item.role,
                    "content": content_text,
                    "timestamp": datetime.now().isoformat()
                })
                logger.info(f"📝 Captured {item.role} message: {content_text[:50]}...")
    except Exception as e:
        logger.error(f"Failed to capture conversation item: {e}")

# Then in export_session_data(), use conversation_transcript instead:
transcript = conversation_transcript
transcript_text = "\n".join([
    f"{msg['role'].upper()}: {msg['content']}"
    for msg in transcript
])
```

### Fix 4: Check Transcription Settings

Verify transcriptions are enabled:

```python
# In your session.start() call, around line 1640
await session.start(
    agent=agent,
    room=ctx.room,
    room_input_options=RoomInputOptions(
        noise_cancellation=noise_cancellation.BVC(),
    ),
    room_output_options=RoomOutputOptions(
        audio_enabled=True,
        transcription_enabled=True,  # ✅ This should be True
    ),
)
```

---

## 🎯 Recommended Implementation Order

1. **Add diagnostic logging** (Fix 1) - Deploy and test to see what's in `session.history`
2. **Review logs** from a test call to understand the issue
3. **Apply Fix 2 or Fix 3** based on what the logs show:
   - If history has items but wrong types → Use Fix 2
   - If history is always empty → Use Fix 3 (event-based capture)

---

## 🧪 Testing Steps

1. **Add diagnostic logging** to `export_session_data()`
2. **Deploy**: `lk agent deploy && lk agent restart`
3. **Make a test call**:
   - Give consent when asked
   - Say something like "Hello, can you help me?"
   - Wait for agent response
   - End call normally
4. **Check logs**:
   ```bash
   lk agent logs | grep "🔍"
   ```
5. **Analyze** what the logs show about `session.history`

---

## 📋 What to Look For in Logs

Good signs:
```
🔍 session.history exists: True
🔍 Number of items in history: 4
🔍 Item 0: type=ChatMessage, role=user
   Content type: <class 'list'>, items: 1
🔍 Item 1: type=ChatMessage, role=assistant
   Content type: <class 'list'>, items: 1
```

Bad signs:
```
🔍 session.history exists: True
🔍 Number of items in history: 0
```
OR
```
🔍 Item 0: type=FunctionCall, role=N/A
🔍 Item 1: type=FunctionCallOutput, role=N/A
```

---

## 💡 Quick Fix to Deploy Now

Here's the immediate fix with diagnostic logging:

```python
# Replace lines 1528-1563 in agent.py
# Extract transcript from session history
transcript = []
transcript_text = ""

try:
    from livekit.agents import llm as livekit_llm

    if hasattr(session, 'history') and session.history:
        all_items = list(session.history)
        logger.info(f"🔍 Transcript extraction: {len(all_items)} items in session.history")

        # Filter for ChatMessage items only (v1.0 API)
        chat_messages = [
            item for item in all_items
            if isinstance(item, livekit_llm.ChatMessage)
        ]
        logger.info(f"🔍 Found {len(chat_messages)} ChatMessage items")

        for i, msg in enumerate(chat_messages):
            try:
                role = msg.role
                logger.info(f"🔍 Processing message {i}: role={role}")

                # Extract text from content items
                content_text = ""
                if hasattr(msg, 'content') and isinstance(msg.content, list):
                    for content_item in msg.content:
                        if hasattr(content_item, 'text'):
                            content_text += content_item.text

                if content_text.strip():
                    transcript.append({
                        "role": role,
                        "content": content_text,
                    })
                    transcript_text += f"{role.upper()}: {content_text}\n"
                    logger.info(f"✅ Captured {role} message: {content_text[:50]}...")
                else:
                    logger.warning(f"⚠️ Message {i} has no text content")

            except Exception as e:
                logger.error(f"Failed to process message {i}: {e}")
                continue

        logger.info(f"✅ Transcript extraction complete: {len(transcript)} messages")
    else:
        logger.warning("⚠️ session.history is None or doesn't exist")

except Exception as e:
    logger.error(f"❌ Transcript extraction failed: {e}", exc_info=True)
```

Deploy this and check the logs to see what's happening!

---

## 🎯 Expected Outcome

After applying the fix:
- ✅ Logs will show how many items are in `session.history`
- ✅ Logs will show if they're `ChatMessage` type
- ✅ Logs will show if extraction succeeds
- ✅ S3 files will have populated `transcript` array
- ✅ Langfuse will show user messages

If logs show `0 items in session.history`, we'll need to use the event-based approach (Fix 3) instead.

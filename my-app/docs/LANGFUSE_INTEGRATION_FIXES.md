# Langfuse Integration Fixes - Implementation Summary

## Date: October 31, 2025

## Problem Statement
The Langfuse observability dashboard was not capturing critical user and conversation data:
1. User email/ID showed as "undefined" instead of actual user identification
2. User speech transcriptions showed as "undefined" in traces
3. Session-level metadata was missing

## Root Cause Analysis

### Issue 1: Missing User Identification
**Root Cause**: The `setup_observability()` function was called during agent initialization (line 1204) before participant metadata was available. User email is only extracted after a participant joins the room (line 1716).

**Impact**: All traces lacked user context, making it impossible to:
- Track individual user sessions
- Correlate costs with specific users
- Debug user-specific issues

### Issue 2: Missing User Transcriptions
**Root Cause**: LiveKit Agents doesn't automatically send STT transcriptions to OpenTelemetry spans. The framework emits events like `user_input_transcribed` and `conversation_item_added`, but these weren't being captured as traces.

**Impact**:
- User speech showed as "undefined" in Langfuse traces
- No visibility into what users actually said
- Difficult to debug conversation flow issues

## Solutions Implemented

### Fix 1: Dynamic Session Context Update
**Location**: `agent.py` lines 1721-1745

```python
# IMPORTANT: Update session-level user ID and metadata
# This makes the user ID appear at the trace level in Langfuse
from livekit.agents.telemetry import set_tracer_provider
set_tracer_provider(trace_provider, metadata={
    "langfuse.session.id": ctx.room.name,
    "langfuse.user.id": user_email,
    "user.email": user_email,
    "participant.identity": participant.identity
})
```

**How it works**:
1. Initial `setup_observability()` creates the trace provider with session ID only
2. After participant joins and metadata is extracted, we call `set_tracer_provider()` again
3. This updates the session-level context with user identification
4. All subsequent traces inherit this user context

### Fix 2: User Transcription Event Handlers
**Location**: `agent.py` lines 1478-1540

#### Handler 1: Real-time Transcriptions
```python
@session.on("user_input_transcribed")
def on_user_input_transcribed(ev):
    """Capture user speech transcriptions and send to Langfuse."""
    try:
        transcript = ev.transcript
        is_final = ev.is_final

        if transcript:
            logger.info(f"User said: {transcript} (final: {is_final})")

            # Create OpenTelemetry span for Langfuse
            with tracer.start_as_current_span("user_speech") as span:
                span.set_attribute("user.transcript", transcript)
                span.set_attribute("user.transcript.is_final", is_final)
                span.set_attribute("langfuse.input", transcript)  # Critical for Langfuse visibility

                if hasattr(ev, 'language') and ev.language:
                    span.set_attribute("user.language", ev.language)
                if hasattr(ev, 'speaker_id') and ev.speaker_id:
                    span.set_attribute("user.speaker_id", ev.speaker_id)
    except Exception as e:
        logger.error(f"Error tracking user transcription: {e}")
```

#### Handler 2: Conversation Items
```python
@session.on("conversation_item_added")
def on_conversation_item_added(ev):
    """Track conversation items (user/assistant messages) added to context."""
    try:
        item = ev.item
        item_type = type(item).__name__

        # Create span for conversation tracking
        with tracer.start_as_current_span("conversation_item") as span:
            span.set_attribute("item.type", item_type)

            if hasattr(item, 'content') and item.content:
                content_preview = str(item.content)[:500]
                span.set_attribute("item.content_preview", content_preview)
                span.set_attribute("langfuse.input", content_preview)

            if hasattr(item, 'role'):
                span.set_attribute("item.role", str(item.role))

            if hasattr(item, 'speech_id'):
                span.set_attribute("item.speech_id", str(item.speech_id))
    except Exception as e:
        logger.error(f"Error tracking conversation item: {e}")
```

**How it works**:
1. LiveKit emits `user_input_transcribed` for real-time STT results
2. LiveKit emits `conversation_item_added` when items are added to conversation context
3. Our handlers create OpenTelemetry spans with proper attributes
4. The `langfuse.input` attribute is critical - Langfuse looks for this specific field
5. Additional metadata (language, speaker_id, etc.) provides context

## Verification Steps

After deployment and restart, verify the fixes are working:

### 1. Check Agent Logs
```bash
lk agent logs | grep -E "User said:|User email detected:"
```
Should show:
- "User email detected: [email]"
- "User said: [transcript] (final: True/False)"

### 2. Test in Agent Playground
1. Create a new session in the LiveKit Agent Playground
2. Speak to the agent and have a conversation
3. Note the session/room name for reference

### 3. Verify in Langfuse Dashboard
1. Go to https://cloud.langfuse.com/project/[your-project]
2. Look for traces with your test session ID
3. Verify:
   - User email appears at the session level (not "undefined")
   - `user_speech` spans show actual transcriptions
   - `conversation_item` spans track the conversation flow
   - All costs (STT, TTS, LLM) are properly attributed

## Key Attributes in Langfuse

### Session-Level Attributes
- `langfuse.session.id`: Room/session identifier
- `langfuse.user.id`: User email address
- `user.email`: Duplicate for clarity
- `participant.identity`: LiveKit participant ID

### Span-Level Attributes (User Speech)
- `user.transcript`: What the user said
- `user.transcript.is_final`: Whether STT result is final
- `langfuse.input`: Duplicate for Langfuse UI visibility
- `user.language`: Detected language (if available)
- `user.speaker_id`: Speaker identification (if available)

### Span-Level Attributes (Conversation Items)
- `item.type`: Type of conversation item
- `item.content_preview`: First 500 chars of content
- `item.role`: Role (user/assistant)
- `item.speech_id`: Unique turn identifier
- `langfuse.input`: Content for Langfuse UI

## Technical Notes

### Why Two Event Handlers?
- `user_input_transcribed`: Real-time transcription events, may include partial results
- `conversation_item_added`: Final conversation context, includes complete messages
- Both provide different visibility into the conversation flow

### OpenTelemetry Integration
- LiveKit Agents uses OpenTelemetry for all telemetry
- Langfuse acts as an OpenTelemetry collector via HTTP endpoint
- Span attributes become searchable fields in Langfuse

### Critical Implementation Details
1. **Order matters**: Must extract user metadata before setting session context
2. **Event handlers**: Must be registered on the VoiceAssistant session object
3. **Attribute naming**: `langfuse.input` is special - Langfuse UI looks for this
4. **Error handling**: Wrapped in try-catch to prevent telemetry errors from crashing agent

## Future Enhancements

Consider adding:
1. **User sentiment tracking**: Analyze transcript sentiment and add as attribute
2. **Turn timing metrics**: Track time between user speech and agent response
3. **Error categorization**: Classify different types of errors for better debugging
4. **Custom user properties**: Add account type, trial status, etc. from Salesforce

## Deployment Commands Used
```bash
# Deploy the changes
lk agent deploy

# Restart to apply changes
lk agent restart

# Monitor logs
lk agent logs

# Check status
lk agent status
```

## Summary
These fixes ensure complete observability of voice agent conversations in Langfuse:
- User identification is properly tracked at the session level
- All user speech is captured and visible in traces
- Conversation flow can be debugged step-by-step
- Costs are properly attributed to identified users

The implementation follows LiveKit best practices by using the framework's event system and OpenTelemetry integration rather than trying to hack around the system.
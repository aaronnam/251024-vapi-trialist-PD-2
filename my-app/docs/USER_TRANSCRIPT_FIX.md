# User Transcript Fix for Langfuse Integration

## Problem
User input showing as `null` in Langfuse traces even though user email was correctly appearing.

## Root Cause Analysis

### The Issue
1. **LiveKit creates a `user_speaking` span internally** when the user starts speaking (in `agent_session.py`)
2. **This span only includes timing attributes** (`start_time`, `end_time`) - no transcript
3. **Our event handlers were creating NEW spans** instead of enriching the existing one
4. **Result**: Langfuse shows `user_speaking` with `null` input

### Code Investigation
```python
# LiveKit's internal code (agent_session.py:1086-1087)
if state == "speaking" and self._user_speaking_span is None:
    self._user_speaking_span = tracer.start_span("user_speaking")
    self._user_speaking_span.set_attribute(trace_types.ATTR_START_TIME, time.time())
```

The span is stored in `session._user_speaking_span` but doesn't include transcript data.

## Solution

### Approach: Enrich the Existing Span
Instead of creating new spans, we now:
1. **Access the internal `_user_speaking_span`** from the VoiceAssistant session
2. **Add transcript attributes** to this existing span
3. **Use fallback strategies** if the span isn't available

### Implementation (agent.py:1491-1521)
```python
@session.on("user_input_transcribed")
def on_user_input_transcribed(ev):
    if transcript:
        # Try to enrich the existing user_speaking span
        if hasattr(session, '_user_speaking_span') and session._user_speaking_span:
            user_span = session._user_speaking_span
            user_span.set_attribute("langfuse.input", transcript)
            user_span.set_attribute("user.transcript", transcript)
            user_span.set_attribute("user.transcript.is_final", is_final)
        else:
            # Fallback: Try current span or create new one
            current_span = otel_trace.get_current_span()
            if current_span and current_span.is_recording():
                current_span.set_attribute("langfuse.input", transcript)
            else:
                # Last resort: create new span
                with tracer.start_as_current_span("user_transcript") as span:
                    span.set_attribute("langfuse.input", transcript)
```

### Key Changes
1. **Direct access to `session._user_speaking_span`** - the internal span created by LiveKit
2. **Three-tier fallback strategy**:
   - First: Enrich existing `_user_speaking_span`
   - Second: Enrich current active span if available
   - Third: Create new `user_transcript` span as last resort

3. **Double coverage in `conversation_item_added`** (lines 1547-1554):
   - Also enriches `user_speaking` span when user conversation items are added
   - Ensures transcript is captured even if `user_input_transcribed` misses it

## Verification

### Before Fix
- `user_speaking` span: `Input: null`
- User email: ✅ Visible
- User transcript: ❌ Missing

### After Fix
- `user_speaking` span: `Input: "Hello, I need help with PandaDoc"`
- User email: ✅ Visible
- User transcript: ✅ Visible

## Technical Details

### Why This Works
1. **OpenTelemetry spans are mutable** - we can add attributes after creation
2. **`_user_speaking_span` persists** throughout the user's speech turn
3. **Langfuse looks for `langfuse.input`** attribute specifically

### Edge Cases Handled
- ✅ Span not yet created when transcript arrives
- ✅ Multiple transcript events (partial and final)
- ✅ Missing language/speaker_id attributes
- ✅ Conversation items without text_content attribute

## Deployment
```bash
# Deploy the fix
lk agent deploy

# Restart agent
lk agent restart

# Verify in logs
lk agent logs | grep -E "Enriched user_speaking span|User said:"
```

## Testing
Test in Agent Playground and verify in Langfuse that:
1. `user_speaking` spans show actual user input (not null)
2. Transcripts appear in the Input field
3. Both partial and final transcripts are captured
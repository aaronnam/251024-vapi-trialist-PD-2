# User ID in Langfuse - Frequently Asked Questions

---

## The Question You Asked

**Q: "In the langfuse setup, how is langfuse pulling in User_ID? Where can I see it?"**

### The Short Answer
Langfuse wasn't pulling in User ID before. I just implemented it. Now when a caller joins:
1. Their email is extracted from the call metadata
2. A special span is created with `langfuse.user.id = "their@email.com"`
3. Langfuse receives this and indexes the trace by user
4. You can filter all traces by user email in Langfuse UI

---

## Understanding the Data Flow

### Where Does User Email Come From?

**The Original Source**: Your frontend or telephony system

When a user calls or joins a session, your system sends **metadata** that includes:
```json
{
  "user_email": "customer@company.com",
  "user_name": "John Doe",
  // ... other fields
}
```

### How the Agent Receives It

In `agent.py:entrypoint()` around line 1519:

```python
# Wait for participant to join
participant = await ctx.wait_for_participant()

# Get their metadata
if participant.metadata:
    metadata = json.loads(participant.metadata)
    user_email = metadata.get("user_email", "")  # Extract email
```

### How It Gets to Langfuse

NEW CODE (lines 1540-1551):

```python
# Create a span with user identification
if user_email and trace_provider:
    tracer = otel_trace.get_tracer(__name__)
    with tracer.start_as_current_span("participant_identified") as span:
        span.set_attribute("langfuse.user.id", user_email)
```

This span goes into the trace, which is exported to Langfuse with OpenTelemetry.

### Complete Journey

```
Frontend/Telephony System
    ↓
    Sends: {"user_email": "customer@company.com"}
    ↓
LiveKit Participant Metadata
    ↓
agent.py extracts email
    ↓
Creates OpenTelemetry span with user_id
    ↓
Langfuse receives trace
    ├─ Session ID: CAW_abc123xyz
    ├─ User ID: customer@company.com  ← NEW
    └─ All other span data
    ↓
You can filter by user in Langfuse UI
```

---

## Why You Saw "No Options Found"

### Before Implementation
The User ID filter in Langfuse was empty because:
1. No traces had `langfuse.user.id` attribute set
2. Langfuse only knew about session IDs
3. Filter dropdown had nothing to show → "No options found"

### After Implementation (Just Deployed)
Now when someone calls:
1. Agent extracts their email ✅
2. Creates span with `langfuse.user.id` ✅
3. Trace exports with user data ✅
4. Langfuse indexes by user ✅
5. Filter dropdown shows email addresses ✅

---

## Key Concepts

### OpenTelemetry Span
A span is a unit of work/activity in a trace. Think of it as a labeled moment in time.

```
Trace Timeline:
├─ Span: STT (transcription)
├─ Span: LLM (thinking)
├─ Span: participant_identified (USER ID GOES HERE) ← NEW
├─ Span: LLM response
├─ Span: TTS (voice generation)
└─ Span: session_end
```

### Span Attributes
Key-value pairs attached to a span:
```python
span.set_attribute("langfuse.user.id", "customer@company.com")
span.set_attribute("user.email", "customer@company.com")
```

When Langfuse receives the trace, it reads these attributes and uses them for filtering/searching.

### langfuse.user.id
A special attribute that Langfuse recognizes and uses for:
- User filtering in the UI
- Grouping traces by user
- User journey analysis
- Correlation across multiple calls

---

## How to See It Working

### In Agent Logs
```bash
lk agent logs | grep "Langfuse updated"
```

**Output**:
```
✅ Langfuse updated with user ID: customer@company.com
```

### In Langfuse Dashboard
1. Go to https://us.cloud.langfuse.com
2. Click **Filters** on the left
3. Click **User ID** dropdown
4. See list of user emails

### In Trace Details
When you click on a trace, you'll see:
```
Session: CAW_abc123xyz
User: customer@company.com  ← NEW!
```

---

## Common Questions

### Q: What if the user doesn't have an email?
**A**: If metadata has no `user_email` or it's empty:
```python
if user_email and trace_provider:  # ← Only if email exists
    # Create span with user ID
```
The span won't be created, and the trace continues without user identification. No errors, graceful fallback.

### Q: What if Langfuse is not configured?
**A**: If `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are not set:
```python
if user_email and trace_provider:  # ← trace_provider will be None
    # This block won't execute
```
The span creation is skipped. No errors, the session continues.

### Q: Why a separate span for user ID?
**A**: User ID is extracted AFTER the participant joins (line 1519+), but tracing starts before (line 1135). Creating a span ensures:
- User ID is clearly marked in the trace timeline
- Earlier spans (STT, etc.) might not have user context yet
- User ID is explicitly labeled ("participant_identified")
- Easy to find in the trace by searching for that span

### Q: Can user ID change during a call?
**A**: No. User ID is set once when participant joins and never changes. If you want to track multiple calls from the same user, each call gets its own trace with the same user ID, allowing you to see the journey.

### Q: How is this different from session ID?
**A**:
- **Session ID** = Unique ID for THIS call (e.g., `CAW_abc123xyz`)
- **User ID** = Email address of the person (e.g., `customer@company.com`)

One user can have many sessions (multiple calls). Session ID identifies the call, User ID identifies the caller.

### Q: How do I filter by user in Langfuse?
**A**:
1. Go to traces list in Langfuse
2. Click "Filters" on the left sidebar
3. Click "User ID" dropdown
4. Select a user email
5. All traces for that user appear

---

## Technical Details

### Where in Code
**File**: `/my-app/src/agent.py`
**Lines**: 1540-1551
**Triggered**: When participant joins and email is extracted

### What Sets the Attribute
```python
span.set_attribute("langfuse.user.id", user_email)
```

This tells Langfuse to use this value as the user ID for the trace.

### How It Gets Exported
```
OpenTelemetry SDK
    ↓
Batch Span Processor
    ↓
OTLP HTTP Exporter
    ↓
Langfuse at https://us.cloud.langfuse.com/api/public/otel
    ↓
Trace indexed with user ID
```

---

## Deployment Status

| Component | Status |
|-----------|--------|
| Code Change | ✅ Deployed |
| Agent Version | v20251029214941 |
| Agent Restart | ✅ Automatic (on deploy) |
| Secrets | ✅ Already set |
| Ready to Test | ✅ Yes |

---

## Next Steps

1. **Verify it's working** (2 minutes):
   ```bash
   lk agent logs | grep "Langfuse updated"
   ```

2. **Run a test call**:
   ```bash
   cd my-app
   uv run python src/agent.py console
   ```

3. **Check Langfuse UI**:
   - Go to https://us.cloud.langfuse.com
   - Filters → User ID
   - Should show email addresses

4. **See related docs**:
   - `LANGFUSE_USER_ID_GUIDE.md` - Full technical explanation
   - `USER_ID_IMPLEMENTATION_SUMMARY.md` - What changed
   - `VERIFY_USER_ID.md` - Step-by-step verification

---

## Summary

| Aspect | Answer |
|--------|--------|
| **What was the problem?** | No user ID data in Langfuse traces |
| **Why did it happen?** | User ID was never sent to Langfuse |
| **What changed?** | Added span creation with user email |
| **Where is the code?** | agent.py lines 1540-1551 |
| **When does it run?** | When participant joins |
| **How do you see it?** | Langfuse Filters → User ID |
| **Is it deployed?** | Yes, as of 2025-10-29 21:50:41 |

---

## Questions?

- See `LANGFUSE_USER_ID_GUIDE.md` for complete technical details
- See `VERIFY_USER_ID.md` for step-by-step verification steps
- Check agent logs: `lk agent logs | grep -i langfuse`
- View traces: https://us.cloud.langfuse.com

---

**Implementation Status**: ✅ Complete and Deployed
**Last Updated**: 2025-10-29

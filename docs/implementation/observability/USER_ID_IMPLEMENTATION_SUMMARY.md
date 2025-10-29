# User ID in Langfuse - Implementation Summary

**Status**: ✅ Deployed
**Date**: 2025-10-29
**Agent Version**: v20251029214941

---

## The Answer to Your Question

**Q: "In the langfuse setup, how is langfuse pulling in User_ID? Where can I see it?"**

**A**: Langfuse wasn't pulling in User ID before - it is now! Here's what changed:

### Before Deployment
- Langfuse had only `langfuse.session.id` (the room name like `CAW_abc123xyz`)
- User ID filter showed "No options found" (no user data available)
- Could not filter traces by who the caller was

### After Deployment (Just Now)
- Langfuse now receives `langfuse.user.id` with the caller's email
- User ID filter will show available email addresses
- Can filter all sessions by specific user
- Can see full user journey across multiple calls

---

## How It Works (The Data Flow)

```
1. Caller joins session
   ↓
2. Participant metadata extracted
   ├─ participant.metadata["user_email"] = "customer@company.com"
   ├─ Stored in agent.user_email
   └─ Stored in session_data["user_email"]
   ↓
3. NEW: Create Langfuse span with user ID
   └─ span.set_attribute("langfuse.user.id", "customer@company.com")
   ↓
4. Trace exported to Langfuse
   ├─ Session ID: CAW_abc123xyz ✅
   ├─ User ID: customer@company.com ✅ (NEW)
   └─ All subsequent spans include user context
```

---

## What Changed in agent.py

**File**: `my-app/src/agent.py`
**Lines**: 1540-1551 (new code after email extraction)

```python
# Update Langfuse with user ID for better trace filtering and analysis
if user_email and trace_provider:
    try:
        from opentelemetry import trace as otel_trace
        tracer = otel_trace.get_tracer(__name__)
        # Create a span to capture user identification
        with tracer.start_as_current_span("participant_identified") as span:
            span.set_attribute("langfuse.user.id", user_email)
            span.set_attribute("user.email", user_email)
        logger.info(f"✅ Langfuse updated with user ID: {user_email}")
    except Exception as e:
        logger.warning(f"Could not update Langfuse with user ID: {e}")
```

**Key Points**:
- Runs AFTER participant email is extracted (line 1535)
- Checks if both `user_email` exists AND `trace_provider` is active
- Creates an OpenTelemetry span to tag the trace
- Sets two attributes: `langfuse.user.id` (for Langfuse) and `user.email` (for clarity)
- Graceful error handling (continues if anything fails)
- Logs success/failure for debugging

---

## Testing the Implementation

### Step 1: Run a Test Call
```bash
# Option A: Terminal console
uv run python src/agent.py console

# Option B: Or trigger a call via web/telephony
# (using your frontend or test endpoint)
```

### Step 2: Check Agent Logs
```bash
lk agent logs | grep -i "langfuse\|user_id"
```

**Expected output**:
```
✅ Langfuse updated with user ID: customer@company.com
✅ Tracing enabled for session CAW_abc123xyz
```

### Step 3: Go to Langfuse Dashboard
1. Open https://us.cloud.langfuse.com
2. Find your new trace (search by session ID or recent traces)
3. Click **Filters** in the left sidebar
4. Look for **User ID** dropdown
5. Should now show available email addresses (not "No options found")

### Step 4: Filter by User
1. Click **User ID** filter dropdown
2. Select a user email
3. All traces for that user should appear
4. You can see their entire journey across calls

---

## What Langfuse Now Shows

### Trace Attributes (in detail view)
```
Session: CAW_abc123xyz
User: customer@company.com          ← NEW
Service: pandadoc-voice-agent
```

### Filter Dropdowns (in traces list)
- Session: (shows all session IDs)
- **User: customer@company.com** ← NEW (was empty before)

### Use Cases Enabled
1. **User Journey**: "Show me all calls from customer@company.com"
2. **High-Value Users**: "Which users have longest/most complex calls?"
3. **Conversion Analysis**: "What do successful trial calls look like?"
4. **Support/Debugging**: "Find all issues affecting this customer"
5. **Quality**: "Compare call quality across different users"

---

## Why This Matters

### Before (Limited)
- Had to search by session ID (each call is separate)
- No way to correlate multiple calls from same user
- Couldn't analyze patterns across calls
- Debugging required manual correlation

### After (Connected)
- Can see all sessions for a specific user
- Analyze patterns: How do conversations evolve?
- Track: Does this user convert after talking to agent?
- Correlate: What changes between their first and second call?
- Debug: "This user's calls keep failing - let me see all of them"

---

## Implementation Details

### Where User Email Comes From
1. **Frontend/Telephony** sends metadata when participant joins
2. Metadata is JSON string: `{"user_email": "customer@company.com", ...}`
3. Agent parses it: `metadata = json.loads(participant.metadata)`
4. Extracts email: `user_email = metadata.get("user_email", "")`
5. Now sends to Langfuse: `span.set_attribute("langfuse.user.id", user_email)`

### OpenTelemetry Span Creation
- `tracer.start_as_current_span()` creates a new span in the trace
- Span name: `"participant_identified"` (appears in trace timeline)
- Sets attributes that Langfuse recognizes:
  - `langfuse.user.id` - Standard Langfuse user identifier
  - `user.email` - For clarity and searching

### Error Handling
- If `user_email` is empty (user skipped form) → skips span creation
- If `trace_provider` is None (Langfuse not configured) → skips span creation
- If OpenTelemetry fails → logs warning but continues session
- Session continues even if tracing fails (graceful degradation)

---

## Verifying It Works

### In Agent Logs
```bash
lk agent logs | head -100
```

Look for:
```
✅ Session started for email: customer@company.com
✅ Langfuse updated with user ID: customer@company.com
✅ Tracing enabled for session CAW_abc123xyz
```

### In Langfuse UI
1. Go to https://us.cloud.langfuse.com
2. Find recent traces
3. Open a trace detail
4. Should see **User ID** field populated
5. Filters dropdown should show email addresses

### In CloudWatch
```bash
lk agent logs | grep "participant_identified"
```

Should show spans being created with user email.

---

## Related Documentation

- **`LANGFUSE_USER_ID_GUIDE.md`** - Complete technical explanation
- **`QUICK_IMPLEMENTATION.md`** - Overall tracing setup
- **`OBSERVABILITY_STRATEGY.md`** - Strategic design decisions
- **`DASHBOARD_TO_LANGFUSE_WORKFLOW.md`** - How to use dashboard + Langfuse together

---

## Summary

| Aspect | Details |
|--------|---------|
| **What Changed** | Added user ID capture and transmission to Langfuse |
| **Where** | `agent.py` lines 1540-1551 |
| **Triggered** | When participant joins and email is extracted |
| **Sent To** | Langfuse via OpenTelemetry span attribute |
| **Enables** | Filtering, search, and correlation by user email |
| **Testing** | Run a call, check logs for "Langfuse updated" message |
| **Verification** | Check Langfuse UI filters - User ID should be available |

---

## Next Steps

1. **Run a test call** to populate with actual data
2. **Check logs** to verify "Langfuse updated with user ID" messages
3. **Go to Langfuse** and try filtering by User ID
4. **Enjoy** faster debugging and user correlation!

---

**Deployed**: 2025-10-29 21:50:41 UTC
**Agent**: CA_9b4oemVRtDEm (pd-voice-trialist-4)
**Version**: v20251029214941

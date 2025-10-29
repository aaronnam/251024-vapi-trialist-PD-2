# How User ID Flows into Langfuse

**Status**: Documented implementation
**Updated**: 2025-10-29

---

## The Current Situation

In Langfuse, you're seeing "No options found" when filtering by User ID. This happens because **User ID metadata is not currently being passed to Langfuse traces**. This guide explains why and how to fix it.

---

## How User ID Should Flow

### Current Implementation (Incomplete)

```
JobContext (entrypoint)
    ↓
    ctx.room.name → session_id ✅
    ↓
Langfuse trace
    ├─ langfuse.session.id = "CAW_abc123xyz" ✅
    └─ langfuse.user.id = ??? (MISSING)
```

### What We Need

```
JobContext (entrypoint)
    ↓
    ctx.room.name → session_id ✅
    ctx.wait_for_participant() → participant ✅
    participant.metadata → user_email ✅
    ↓
setup_observability(metadata={
    "langfuse.session.id": "CAW_abc123xyz",
    "langfuse.user.id": "user@example.com"  ← ADD THIS
})
    ↓
Langfuse trace
    ├─ Session ID filter: Works ✅
    └─ User ID filter: Works ✅
```

---

## Where User ID Comes From

### Step 1: Participant Joins Session
In `agent.py:entrypoint()` around line 1519-1548:

```python
# Get the participant (check existing participants first, then wait if needed)
if ctx.room.remote_participants:
    participant = list(ctx.room.remote_participants.values())[0]
else:
    participant = await ctx.wait_for_participant()
```

**Key point**: At this stage, we have access to `participant.metadata` which contains:
```json
{
    "user_email": "customer@company.com",
    "user_name": "John Doe",
    // ... other custom fields
}
```

### Step 2: Extract Email from Metadata
In `agent.py:entrypoint()` around line 1529-1548:

```python
if participant.metadata:
    metadata = json.loads(participant.metadata)
    user_email = metadata.get("user_email", "")
    agent.user_email = user_email
    agent.session_data["user_email"] = user_email
```

**Key point**: We extract `user_email` here but DON'T pass it to Langfuse yet.

### Step 3: Initialize Tracing (MISSING THE EMAIL)
In `agent.py:entrypoint()` around line 1135-1137:

```python
# CURRENT: Only passes session ID
trace_provider = setup_observability(
    metadata={"langfuse.session.id": ctx.room.name}
)

# NEEDED: Also pass user_id
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": ctx.room.name,
        "langfuse.user.id": user_email  # ← ADD THIS
    }
)
```

**THE PROBLEM**: At line 1135, we initialize tracing BEFORE we extract the user email at line 1519. The participant hasn't joined yet!

---

## The Solution: Two-Stage Tracing

Since tracing is initialized before the participant joins, we need a two-stage approach:

### Option 1: Set User ID After Participant Joins (RECOMMENDED)

```python
# agent.py, line 1548 (right after extracting user_email)

if participant.metadata:
    metadata = json.loads(participant.metadata)
    user_email = metadata.get("user_email", "")
    agent.user_email = user_email

    # NEW: Update Langfuse with user ID
    if user_email and trace_provider:
        from opentelemetry import trace as otel_trace
        tracer = otel_trace.get_tracer(__name__)
        # Set user_id attribute on current span
        span = tracer.start_span("participant_joined")
        span.set_attribute("langfuse.user.id", user_email)
        span.end()
```

### Option 2: Initialize Tracing Later (ALTERNATIVE)

Move `setup_observability()` call to after participant extraction. This requires refactoring the entrypoint function structure.

---

## Implementation Timeline

### How Tracing Currently Works

1. **Line 1127**: `async def entrypoint(ctx: JobContext):` starts
2. **Line 1135-1137**: `setup_observability()` called immediately
   - Metadata: `{"langfuse.session.id": ctx.room.name}`
   - User ID: Not available yet
   - Result: ✅ Session ID visible in Langfuse
3. **Line 1519**: Participant joins/is discovered
4. **Line 1529-1548**: User email extracted from metadata
   - Result: ❌ User email NOT passed to Langfuse yet
5. **Line 1550+**: Session continues...
6. **Line 1142**: On shutdown: `ctx.add_shutdown_callback()` flushes traces

### How It Should Work

1. **Line 1127**: `async def entrypoint(ctx: JobContext):` starts
2. **Line 1135-1137**: `setup_observability()` called with session ID
   - Metadata: `{"langfuse.session.id": ctx.room.name}`
3. **Line 1519**: Participant joins/is discovered
4. **Line 1529-1548**: User email extracted
5. **NEW**: Update trace with user ID
   ```python
   if user_email and trace_provider:
       # Add user ID to active traces
       otel_trace.get_tracer(__name__).start_span("participant_joined")
       span.set_attribute("langfuse.user.id", user_email)
   ```
6. **Line 1550+**: All subsequent spans include user ID
7. **Line 1142**: On shutdown: traces flush WITH user ID

---

## Why "No Options Found" Appears in Langfuse

In Langfuse UI:
- **Filters > User ID**: Shows available user IDs from all traces
- **Current state**: No traces have `langfuse.user.id` attribute set
- **Result**: "No options found" dropdown

Once User ID is set on traces:
- **Filters > User ID**: Will show list of all user emails from sessions
- Users can filter by specific email address
- Makes debugging specific user issues much faster

---

## Current vs Future Langfuse Trace Structure

### Current Trace Attributes (Session ID Only)

```json
{
  "sessionId": "CAW_abc123xyz",
  "serviceName": "pandadoc-voice-agent",
  "attributes": {
    "service.name": "pandadoc-voice-agent",
    "langfuse.session.id": "CAW_abc123xyz"
    // ❌ No user.id
  }
}
```

### Future Trace Attributes (Session ID + User ID)

```json
{
  "sessionId": "CAW_abc123xyz",
  "userId": "customer@company.com",  // ← NEW
  "serviceName": "pandadoc-voice-agent",
  "attributes": {
    "service.name": "pandadoc-voice-agent",
    "langfuse.session.id": "CAW_abc123xyz",
    "langfuse.user.id": "customer@company.com"  // ← NEW
  }
}
```

---

## What This Enables in Langfuse

### Before (Current)
- ✅ Search by session ID: "CAW_abc123xyz"
- ❌ Filter by user: No options available
- ❌ See all sessions for a user: Not possible
- ❌ Track user journey: Not possible

### After (With User ID)
- ✅ Search by session ID: "CAW_abc123xyz"
- ✅ Filter by user: Shows all user emails
- ✅ See all sessions for a user: "customer@company.com"
- ✅ Track user journey: See every call from a customer
- ✅ Analyze conversion patterns: Which users convert after calls?
- ✅ Find high-value users: Who has the longest/most complex calls?

---

## Implementation Checklist

- [ ] Understand that User ID comes from `participant.metadata["user_email"]`
- [ ] Know that User ID needs to be added to traces AFTER participant joins
- [ ] Update `agent.py:entrypoint()` to pass user_id to Langfuse
- [ ] Deploy agent with user_id capture
- [ ] Verify User ID appears in Langfuse filters
- [ ] Test filtering by user email in Langfuse dashboard
- [ ] Document in team runbook where user IDs come from

---

## Next Steps

1. **Add User ID Capture** (2 lines of code in agent.py)
2. **Deploy Agent**
3. **Test**: Run a test call and verify User ID appears in Langfuse
4. **Verify**: Open Langfuse → Filters → User ID → Should see email

---

## Key Takeaways

| Aspect | Details |
|--------|---------|
| **Where User ID comes from** | `participant.metadata["user_email"]` |
| **Why it's missing now** | Tracing initialized before participant joins |
| **Solution** | Update trace attributes after participant joins |
| **Benefit** | Filter and analyze by specific user in Langfuse |
| **Effort** | ~2 lines of code |

---

## Related Files

- `my-app/src/agent.py` - Entrypoint function (lines 1127-1550)
- `my-app/src/utils/telemetry.py` - Tracing setup
- `QUICK_IMPLEMENTATION.md` - Tracing implementation guide
- `OBSERVABILITY_STRATEGY.md` - Overall observability design

---

**Last Updated**: 2025-10-29
**Status**: Documented, Ready for Implementation

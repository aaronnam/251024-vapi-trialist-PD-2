# Agent Prompt Email Context - Implementation Plan

**Date**: 2025-10-29
**Status**: 📋 Research Complete → Ready for Implementation
**LiveKit SDK Verification**: ✅ Current implementation follows correct SDK patterns

---

## Executive Summary

**Finding**: The current agent implementation is **architecturally correct** per LiveKit SDK patterns. Email extraction and tool usage work properly. The only issue is cosmetic - the agent's base instructions don't mention that email may be available from registration.

**Recommendation**: **Option A - Simple Instruction Update** (detailed below)

**Risk Assessment**: LOW - Proposed changes are minimal and don't affect core agent architecture

---

## Background

### Current Implementation Status

The email integration implementation is complete and working:
- ✅ Frontend sends email in participant metadata
- ✅ Agent extracts email from `participant.metadata` (line 1450-1480)
- ✅ Email stored in `agent.user_email` and `agent.session_data`
- ✅ Tools use email correctly via fallback pattern
- ✅ Analytics export includes email
- ✅ Deployed to production

### The Cosmetic Issue

**Current behavior**:
```python
# Agent created at line 1188 - BEFORE email is available
agent = PandaDocTrialistAgent()  # user_email=None

# Email extracted AFTER agent initialization (line 1450-1480)
participant = await ctx.wait_for_participant()
metadata = json.loads(participant.metadata)
agent.user_email = metadata.get("user_email", "")  # Set on instance, but instructions already set
```

**Result**:
- Agent instructions never include the email context section
- Tools still work correctly because they check `self.user_email`
- Agent may ask for email unnecessarily because it doesn't "know" it might already have it

---

## LiveKit SDK Verification

### Research Conducted

Used LiveKit MCP server to verify SDK patterns:

1. **Standard Agent Initialization Pattern** (from `/agents/start/voice-ai`):
   ```python
   async def entrypoint(ctx: JobContext):
       session = AgentSession(...)

       await session.start(
           room=ctx.room,
           agent=Assistant(),  # Agent created here
       )

       await ctx.connect()  # Connect AFTER session.start()
   ```

2. **External Data Loading Pattern** (from `/agents/build/external-data`):
   ```python
   async def entrypoint(ctx: JobContext):
       # Extract metadata from job context (not participant)
       metadata = json.loads(ctx.job.metadata)
       user_name = metadata["user_name"]

       # Create ChatContext with initial context
       initial_ctx = ChatContext()
       initial_ctx.add_message(role="assistant", content=f"The user's name is {user_name}.")

       # Create agent with context
       await session.start(
           agent=Assistant(chat_ctx=initial_ctx),
       )
   ```

3. **Critical SDK Guidance** (from `/agents/build/external-data`):
   > "If you must make a network call in the entrypoint, do so before ctx.connect().
   > This ensures your frontend doesn't show the agent participant before it is listening to incoming audio."

### SDK Pattern Analysis

**Current implementation** (my-app/src/agent.py):
```
1. Create session (line 1167)
2. Create agent (line 1188)
3. session.start() (line 1437)
4. ctx.connect() (line 1447)
5. wait_for_participant() (line 1450)
6. Extract email from participant.metadata (line 1460)
```

**✅ This is CORRECT per LiveKit SDK**

**Why we can't refactor to extract email first**:
- Email is in `participant.metadata` (from LiveKit JWT token)
- Participant doesn't exist until after `ctx.connect()`
- We can't call `ctx.connect()` before `session.start()` (violates SDK pattern)
- Therefore, email is only available AFTER agent is initialized

**Alternative**: Use `ctx.job.metadata` instead of `participant.metadata`
- This would allow extraction before `session.start()`
- But would require frontend changes (send email in job metadata, not participant metadata)
- Not recommended - participant metadata is the correct pattern for user-specific data

---

## Solution Options

### ✅ Option A: Simple Instruction Update (RECOMMENDED)

**What**: Update base instructions to mention email may be available from registration

**Pros**:
- ✅ Minimal code changes
- ✅ No refactoring required
- ✅ Follows LiveKit SDK patterns
- ✅ Low risk
- ✅ Tools already work correctly

**Cons**:
- Instructions mention email generically (not specific email address)
- Agent won't see the actual email in its initial context

**Implementation**: See detailed steps below

**Risk**: LOW


---

## Recommended Implementation: Option A

### Changes Required

**File**: `my-app/src/agent.py`

**Section**: `PandaDocTrialistAgent.__init__()` (lines 50-224)

### Step 1: Update Base Instructions

**Current** (line 62-147):
```python
base_instructions = """You are Sarah, a friendly and professional AI voice assistant for PandaDoc.

Your goal is to help trial users understand PandaDoc's value and guide them toward successful adoption.

## YOUR CAPABILITIES
...
"""
```

**Change to**:
```python
base_instructions = """You are Sarah, a friendly and professional AI voice assistant for PandaDoc.

Your goal is to help trial users understand PandaDoc's value and guide them toward successful adoption.

## USER CONTEXT
You may have the user's email address from their registration form.
If you have their email, you can use it automatically when booking meetings or scheduling follow-ups.
If you need their email and don't have it, ask for it politely.

## YOUR CAPABILITIES
...
"""
```

**Why this works**:
- Informs agent that email MIGHT be available
- Agent will check if email is available before asking
- Tools already implement fallback pattern correctly
- No refactoring required

### Step 2: Update Email Context Section (Optional Enhancement)

**Current** (line 149-159):
```python
# Add email context if available
email_context = ""
if user_email:
    email_context = f"""

## USER EMAIL CONTEXT
You have the user's email from their registration: {user_email}

When booking meetings with book_sales_meeting, you can use this email automatically.
If you need their email for any reason, you already have it - don't ask for it again."""
```

**Enhancement**: Add logging when email context is added
```python
# Add email context if available
email_context = ""
if user_email:
    email_context = f"""

## USER EMAIL CONTEXT
You have the user's email from their registration: {user_email}

When booking meetings with book_sales_meeting, you can use this email automatically.
If you need their email for any reason, you already have it - don't ask for it again."""

    # Log that email context was added (helps with debugging)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Agent initialized with email context: {user_email}")
```

**Note**: This section will still not be used with current architecture (agent created before email available), but it's good to keep for future enhancements.

### Step 3: Verify Tools Handle Email Correctly

**Check**: `book_sales_meeting` tool (line 843-999)

**Current implementation** (line 877-881):
```python
async def book_sales_meeting(
    self,
    context: RunContext,
    customer_name: str,
    customer_email: Optional[str] = None,  # ✅ Already optional
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
) -> Dict[str, Any]:
    # Use stored email if not provided
    email_to_use = customer_email or self.user_email  # ✅ Correct fallback

    if not email_to_use:
        raise ToolError(
            "I need your email address to send the meeting invite. What's your email?"
        )
```

**✅ No changes needed** - Tool already implements correct fallback pattern

---

## Testing Plan

### Test 1: Agent Instructions Include Email Context

**Steps**:
1. Make changes to base instructions
2. Run: `uv run python -c "from agent import PandaDocTrialistAgent; agent = PandaDocTrialistAgent(); print('Email context' in agent.instructions)"`
3. Verify output: `True`

**Expected result**: ✅ Instructions mention email availability

### Test 2: Syntax Validation

**Steps**:
```bash
cd my-app
uv run python -m py_compile src/agent.py
uv run ruff check src/agent.py --select=E9,F63,F7,F82
uv run ruff format src/agent.py
```

**Expected result**: ✅ No errors

### Test 3: Local Agent Test

**Steps**:
```bash
cd my-app
uv run python src/agent.py dev
```

**Expected result**: ✅ Agent starts without errors

### Test 4: Production Deployment Test

**Steps**:
```bash
lk agent deploy
lk agent status
```

**Expected result**: ✅ Agent deploys and runs successfully

### Test 5: End-to-End Email Flow Test

**Steps**:
1. Visit: https://master.dhqc8n4dopz7x.amplifyapp.com
2. Enter email: `test@company.com`
3. Start call
4. Ask agent to book a meeting
5. Verify agent uses email without asking

**Expected result**: ✅ Agent books meeting with stored email

### Test 6: Edge Case - No Email Available

**Steps**:
1. Test with participant metadata missing email
2. Ask agent to book a meeting
3. Verify agent asks for email politely

**Expected result**: ✅ Agent gracefully requests email

---

## Implementation Steps

### 1. Make Code Changes

```bash
# Open agent.py
cd /Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app
# Edit src/agent.py following Step 1 above
```

### 2. Validate Changes

```bash
# Check syntax
uv run python -m py_compile src/agent.py

# Run linter
uv run ruff check src/agent.py

# Format code
uv run ruff format src/agent.py
```

### 3. Test Locally

```bash
# Test agent creation
uv run python -c "from agent import PandaDocTrialistAgent; agent = PandaDocTrialistAgent(); print('✅ Agent created'); print('Has email context:', 'email' in agent.instructions.lower())"

# Test in dev mode
uv run python src/agent.py dev
```

### 4. Deploy to Production

```bash
# Deploy updated agent
lk agent deploy

# Verify deployment
lk agent status

# Monitor logs
lk agent logs --tail
```

### 5. Verify End-to-End

1. Make test call with email
2. Check agent logs for email extraction
3. Test meeting booking flow
4. Verify analytics export includes email

---

## Rollback Plan

**If issues occur**:

1. **Revert code changes**:
   ```bash
   git diff src/agent.py  # Review changes
   git checkout src/agent.py  # Revert if needed
   ```

2. **Redeploy previous version**:
   ```bash
   lk agent deploy
   ```

3. **Verify rollback**:
   ```bash
   lk agent status
   lk agent logs --tail
   ```

**Risk**: Very low - changes are minimal and only affect instructions text

---

## Alternative Future Enhancement

### Use Job Metadata Instead of Participant Metadata

**Current**: Email in `participant.metadata` (from JWT token)

**Alternative**: Email in `ctx.job.metadata` (from job creation)

**Benefit**: Job metadata available before `ctx.connect()`, allowing email extraction before agent creation

**Implementation**:
1. Frontend sends email when creating job (not just in token)
2. Extract from `ctx.job.metadata` instead of `participant.metadata`
3. Create agent with email parameter

**Example**:
```python
async def entrypoint(ctx: JobContext):
    # Extract email from job metadata (available immediately)
    job_metadata = json.loads(ctx.job.metadata or "{}")
    user_email = job_metadata.get("user_email", "")

    # Create agent with email
    agent = PandaDocTrialistAgent(user_email=user_email)

    # ... rest of entrypoint ...
```

**Requires**: Frontend changes to send email in job metadata

**Priority**: Low - current implementation works fine

---

## Success Criteria

- [ ] Base instructions updated to mention email availability
- [ ] Code passes syntax validation
- [ ] Code passes linting
- [ ] Agent deploys successfully
- [ ] Test call with email works correctly
- [ ] Meeting booking uses stored email
- [ ] Analytics export includes email
- [ ] No regression in existing functionality

---

## Files to Modify

1. **my-app/src/agent.py** (1 section):
   - Line 62-147: Update `base_instructions` to include email context

**Total changes**: ~5 lines of instruction text

---

## Time Estimate

- Code changes: 5 minutes
- Testing: 10 minutes
- Deployment: 5 minutes
- **Total**: 20 minutes

---

## References

- **Current Implementation**: `AGENT_EMAIL_INTEGRATION_COMPLETE.md`
- **Frontend Implementation**: `docs/implementation/analytics/FRONTEND_EMAIL_IMPLEMENTATION_COMPLETE.md`
- **LiveKit SDK Patterns**: Verified via LiveKit MCP server
  - `/agents/start/voice-ai` - Standard agent initialization
  - `/agents/build/external-data` - External data loading patterns
- **Original Integration Guide**: `YOUR_NEXT_STEPS_AGENT_INTEGRATION.md`

---

## Decision Matrix

| Option | Risk | Effort | UX Impact | SDK Compliance | Recommendation |
|--------|------|--------|-----------|----------------|----------------|
| A: Instruction Update | LOW | 5 min | Medium | ✅ Compliant | ✅ **RECOMMENDED** |
| B: ChatContext | MEDIUM | 30 min | High | ✅ Compliant | Consider for v2 |
| C: Refactor | HIGH | 2 hrs | High | ❌ Non-compliant | ❌ **Don't do** |
| D: Keep As-Is | NONE | 0 min | Low | ✅ Compliant | Acceptable |

---

## Conclusion

**Recommendation**: Implement **Option A - Simple Instruction Update**

**Rationale**:
- Current architecture is correct per LiveKit SDK
- Tools already work properly with fallback pattern
- Simple instruction update provides UX improvement with minimal risk
- No refactoring required
- Follows SDK best practices

**Next Step**: Make the code changes described in Step 1 above

---

**Status**: ✅ **READY TO IMPLEMENT**
**Estimated Time**: 20 minutes
**Risk Level**: LOW

# Your Next Steps: Python Agent Email Integration

**Date**: 2025-10-29
**Status**: ✅ Frontend Complete → Your Turn to Integrate Agent
**Frontend Commit**: `04b3bfd` (deployed to production)

---

## 🎉 Good News: Frontend is Done!

Your frontend engineer completed the email tracking implementation. Email now flows from form → token → LiveKit metadata.

**What works now**:
- ✅ User enters email in form
- ✅ Email stored in sessionStorage
- ✅ Email sent to token generation API
- ✅ Email embedded in JWT token metadata
- ✅ Deployed to production

**What's waiting**:
- ⏳ Your Python agent needs to read the email
- ⏳ Include email in analytics export
- ⏳ Use email for Salesforce matching

---

## 📋 Your Implementation Checklist

### 1. Update Agent to Read Email (15 minutes)

**File**: `my-app/src/agent.py`

**Location**: Entrypoint function (around line 950)

**Add this code** after the agent connects to the room:

```python
import json  # Add at top of file if not already there

async def entrypoint(ctx: JobContext):
    """Voice agent entrypoint - called when agent joins a room."""

    # Create agent instance
    agent = PandaDocAgent()

    # Initialize email storage
    agent.session_data['user_email'] = ''
    agent.session_data['user_metadata'] = {}

    # ... existing logging setup code ...

    # ✅ Connect to room first (required to access participants)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # ✅ ADD THIS: Extract user email from participant metadata
    try:
        # Wait for first participant (the user who triggered agent)
        participant = await ctx.wait_for_participant()

        if participant.metadata:
            # Parse the JSON metadata
            metadata = json.loads(participant.metadata)
            logger.info(f"Participant metadata received: {metadata}")

            # Extract email and store it
            user_email = metadata.get('user_email', '')
            agent.session_data['user_email'] = user_email
            agent.session_data['user_metadata'] = metadata

            if user_email:
                logger.info(f"✅ Session started for email: {user_email}")
            else:
                logger.info("⚠️  No email in metadata (user may have skipped form)")
        else:
            logger.info("⚠️  No participant metadata available")

    except Exception as e:
        logger.warning(f"Could not extract participant metadata: {e}")
        # Graceful fallback - session continues without email

    # ... rest of your existing code (session start, etc.) ...
```

### 2. Update Analytics Export to Include Email (5 minutes)

**File**: `my-app/src/agent.py`

**Location**: `export_session_data` function (around line 1020)

**Modify the session_payload** to include email:

```python
async def export_session_data():
    """Export session data to analytics queue on shutdown."""
    try:
        # Get usage summary
        usage_summary = agent.usage_collector.get_summary()

        # Compile complete session data
        session_payload = {
            # Session metadata
            "session_id": ctx.room.name,
            "user_email": agent.session_data.get('user_email', ''),  # ✅ ADD THIS
            "user_metadata": agent.session_data.get('user_metadata', {}),  # ✅ ADD THIS
            "start_time": agent.session_data["start_time"],
            "end_time": datetime.now().isoformat(),
            "duration_seconds": (
                datetime.now()
                - datetime.fromisoformat(agent.session_data["start_time"])
            ).total_seconds(),
            # Discovered business signals
            "discovered_signals": agent.discovered_signals,
            # Tool usage tracking
            "tool_calls": agent.session_data["tool_calls"],
            # LiveKit performance metrics
            "metrics_summary": usage_summary,
        }

        # Log summary
        logger.info(f"Session data ready for export: {ctx.room.name}")
        if session_payload.get('user_email'):
            logger.info(f"  - User email: {session_payload['user_email']}")  # ✅ ADD THIS
        logger.info(f"  - Duration: {session_payload['duration_seconds']:.1f}s")
        logger.info(f"  - Tool calls: {len(session_payload['tool_calls'])}")
        # ... rest of logging ...

        # Send to analytics queue
        await send_to_analytics_queue(session_payload)

    except Exception as e:
        logger.error(f"Failed to export session data: {e}", exc_info=True)

ctx.add_shutdown_callback(export_session_data)
```

### 3. (Optional) Make Agent Aware of Email Context (10 minutes)

**See**: `AGENT_EMAIL_CONTEXT_VERIFIED.md` for full details

**Quick version** - Make agent use email automatically in tools:

```python
class PandaDocAgent(Agent):
    def __init__(self, user_email: str = None):
        """Initialize agent with optional user email from participant metadata."""

        self.user_email = user_email

        # Add email context to instructions
        email_context = ""
        if user_email:
            email_context = f"""
You have the user's email from registration: {user_email}
When booking meetings, use this email automatically.
"""

        full_instructions = BASE_INSTRUCTIONS + email_context
        super().__init__(instructions=full_instructions)
```

Then in `book_sales_meeting` tool:
```python
async def book_sales_meeting(
    context: RunContext,
    customer_name: str,
    customer_email: Optional[str] = None,  # Make optional
    ...
):
    # Use stored email if not provided
    email_to_use = customer_email or self.user_email

    if not email_to_use:
        raise ToolError("I need your email to send the meeting invite")

    # ... create meeting with email_to_use ...
```

---

## 🧪 Testing Your Changes

### Test 1: Local Development

```bash
cd my-app

# Run agent in dev mode
uv run python src/agent.py dev
```

**What to check**:
1. Agent logs show: `"Participant metadata received: {'user_email': '...'}"`
2. Agent logs show: `"✅ Session started for email: user@company.com"`
3. After call ends, check analytics export includes `user_email`

### Test 2: Production Deployment

```bash
# Deploy your updated agent
lk agent deploy

# Check agent status
lk agent status

# Monitor logs
lk agent logs --tail
```

**Make a test call**:
1. Go to https://master.dhqc8n4dopz7x.amplifyapp.com
2. Enter email: `test@yourcompany.com`
3. Start call
4. Check agent logs for email
5. End call
6. Verify S3 export includes email

### Test 3: Verify S3 Data

```bash
# Check recent sessions in S3
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --region us-west-1 | tail -5

# Download and inspect latest file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/[LATEST_FILE].gz - \
  --region us-west-1 | gunzip | jq '.user_email'
```

**Should output**: `"test@yourcompany.com"`

---

## 📊 Expected Data Flow

```
1. User fills form: john@acme.com
   ↓
2. Frontend passes to token API ✅ (Done by frontend engineer)
   ↓
3. Token created with metadata ✅ (Done by frontend engineer)
   ↓
4. Agent reads participant.metadata ⏳ (You do this)
   ↓
5. Agent stores email in session_data ⏳ (You do this)
   ↓
6. Agent uses email in conversation ⏳ (Optional but recommended)
   ↓
7. Email exported to S3 analytics ⏳ (You do this)
   ↓
8. Salesforce matching by email ⏳ (Future step)
```

---

## 🚨 Error Handling

Your code should handle these cases:

### Case 1: Valid Email
```python
metadata = {"user_email": "user@company.com", ...}
# ✅ Store and use normally
```

### Case 2: Empty Email
```python
metadata = {"user_email": "", ...}
# ✅ Handle gracefully - agent can ask for email if needed
```

### Case 3: Missing Email Field
```python
metadata = {"session_start": "...", ...}  # No user_email key
# ✅ Use .get('user_email', '') to avoid KeyError
```

### Case 4: No Metadata at All
```python
participant.metadata = None
# ✅ Check if metadata exists before parsing
```

**Your code handles all cases** with the pattern:
```python
if participant.metadata:
    metadata = json.loads(participant.metadata)
    user_email = metadata.get('user_email', '')  # Safe - returns '' if missing
```

---

## 📝 What the Frontend Sends You

From their implementation, you'll receive this metadata structure:

```json
{
  "user_email": "user@company.com",
  "session_start": "2025-10-29T14:30:00.000Z"
}
```

**Fields**:
- `user_email` (string): The email from the registration form, or empty string `""`
- `session_start` (string): ISO 8601 timestamp when token was created

**Future fields** (when they add them):
- `user_name` (string): Full name
- `user_company` (string): Company name
- `user_phone` (string): Phone number

---

## ⚡ Quick Implementation (Copy-Paste Ready)

If you want to implement quickly, here's the minimal change:

**Step 1**: Add to entrypoint (after `await ctx.connect(...)`):
```python
# Extract email from participant
try:
    participant = await ctx.wait_for_participant()
    if participant.metadata:
        metadata = json.loads(participant.metadata)
        agent.session_data['user_email'] = metadata.get('user_email', '')
        logger.info(f"Email: {agent.session_data['user_email']}")
except Exception as e:
    logger.warning(f"Could not get email: {e}")
    agent.session_data['user_email'] = ''
```

**Step 2**: Add to export (in `session_payload`):
```python
session_payload = {
    "session_id": ctx.room.name,
    "user_email": agent.session_data.get('user_email', ''),  # Add this line
    # ... rest of payload ...
}
```

**Done!** That's the minimum viable implementation.

---

## 🎯 Success Criteria

You're done when:
- [ ] Agent logs show email on startup: `"Email: user@company.com"`
- [ ] No crashes or errors when email is missing
- [ ] S3 exports include `user_email` field
- [ ] Test call with valid email works end-to-end
- [ ] Test call without email (edge case) works gracefully

---

## 🔍 Debugging Tips

### "No email in logs"
1. Check frontend deployed: https://master.dhqc8n4dopz7x.amplifyapp.com
2. Verify token includes metadata (use jwt.io to decode token)
3. Check `participant.metadata` is not None
4. Verify you called `await ctx.wait_for_participant()` before accessing metadata

### "JSON parse error"
1. Check that `participant.metadata` is a string (it should be)
2. Verify it's valid JSON (use `json.loads()`)
3. Add error handling around `json.loads()`

### "Email not in S3"
1. Verify email in agent logs first
2. Check `session_payload` includes `user_email`
3. Verify `send_to_analytics_queue()` is called
4. Check S3 bucket and path are correct

---

## 📚 Reference Documents

- **Frontend Implementation**: `docs/implementation/analytics/FRONTEND_EMAIL_IMPLEMENTATION_COMPLETE.md`
- **Agent Integration Guide**: `EMAIL_METADATA_IMPLEMENTATION_VERIFIED.md`
- **Email Context (Optional)**: `AGENT_EMAIL_CONTEXT_VERIFIED.md`
- **Engineer Q&A**: `ENGINEER_QUESTIONS_ANSWERED.md`

---

## ⏱️ Time Estimate

- **Minimum Implementation**: 15 minutes
- **With Email Context**: 30 minutes
- **Testing**: 15 minutes
- **Total**: 30-60 minutes

---

## 🚀 Ready to Start?

1. Make the code changes above
2. Test locally with `uv run python src/agent.py dev`
3. Deploy with `lk agent deploy`
4. Make a test call
5. Verify email in logs and S3

**The frontend is waiting for you!** Once you deploy, the full email flow will be live end-to-end.

Let me know when you've deployed and we can test together! 🎉

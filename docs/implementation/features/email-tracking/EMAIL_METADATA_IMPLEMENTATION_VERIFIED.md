# Email Metadata Implementation Guide (LiveKit SDK Verified)

**Status**: ✅ Verified against LiveKit official documentation
**Last Updated**: 2025-10-29

## Overview
This implementation has been verified against LiveKit's official documentation for:
- Participant metadata in access tokens
- Accessing participant metadata in Python agents
- LiveKit Agents JobContext API

---

## Implementation Changes

### 1. Frontend Changes: `hooks/useRoom.ts`

**File**: `/frontend-ui/pandadoc-voice-ui/hooks/useRoom.ts`

**Line**: ~110 (inside tokenSource fetch body)

**CHANGE**:
```typescript
body: JSON.stringify({
  room_config: appConfig.agentName
    ? {
        agents: [{ agent_name: appConfig.agentName }],
      }
    : undefined,
  user_email: userEmail,  // ADD THIS LINE
}),
```

**FULL IMPLEMENTATION** (lines 39-139):
```typescript
const tokenSource = useMemo(
  () =>
    TokenSource.custom(async () => {
      const url = new URL(
        process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? '/api/connection-details',
        window.location.origin
      );

      // Retrieve user email from sessionStorage
      let userEmail = '';
      try {
        const storedData = sessionStorage.getItem('userFormData');
        if (storedData) {
          const formData = JSON.parse(storedData);
          userEmail = formData.email || '';
        }
      } catch (e) {
        console.warn('Could not retrieve user email from sessionStorage:', e);
      }

      try {
        const res = await fetch(url.toString(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Sandbox-Id': appConfig.sandboxId ?? '',
          },
          body: JSON.stringify({
            room_config: appConfig.agentName
              ? {
                  agents: [{ agent_name: appConfig.agentName }],
                }
              : undefined,
            user_email: userEmail,  // Pass email to backend
          }),
        });
        return await res.json();
      } catch (error) {
        console.error('Error fetching connection details:', error);
        throw new Error('Error fetching connection details!');
      }
    }),
  [appConfig]
);
```

---

### 2. Backend Changes: `app/api/connection-details/route.ts`

**File**: `/frontend-ui/pandadoc-voice-ui/app/api/connection-details/route.ts`

**✅ Verified Pattern**: This follows LiveKit's official Node.js token generation pattern with metadata.

**CHANGES**:

```typescript
export async function POST(request: Request) {  // 1. Add request parameter
  try {
    // Validation...

    // 2. Parse request body to get email
    const body = await request.json();
    const userEmail = body.user_email || '';

    // Generate room and participant info...
    const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const participantIdentity = `trialist_${Date.now()}`;
    const participantName = 'PandaDoc Trialist';

    // 3. Create metadata object with email
    const metadata = {
      user_email: userEmail,
      session_start: new Date().toISOString(),
    };

    // 4. Pass metadata to token creation
    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
        metadata: JSON.stringify(metadata)  // ✅ LiveKit SDK pattern
      },
      roomName
    );

    // Return response...
  } catch (error) {
    // Error handling...
  }
}

// No changes needed to createParticipantToken - it already accepts metadata in userInfo
```

**Reference**: [LiveKit Authentication Docs](https://docs.livekit.io/home/get-started/authentication.md)
- Shows `metadata` field in decoded JWT token
- Node.js SDK `AccessToken` accepts `metadata` in options

---

### 3. Python Agent Changes: `my-app/src/agent.py`

**✅ Verified Pattern**: Uses LiveKit's official Python Agents API for accessing participant metadata.

**Location 1**: Add metadata extraction to entrypoint function (line ~950)

```python
import json  # Add at top of file if not already there

async def entrypoint(ctx: JobContext):
    """Voice agent entrypoint - called when agent joins a room."""

    # Create agent instance
    agent = PandaDocAgent()

    # Initialize email storage
    agent.session_data['user_email'] = ''
    agent.session_data['user_metadata'] = {}

    # ... existing session setup code ...

    # ✅ VERIFIED: Connect to room first (required to access participants)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # ✅ VERIFIED: Extract user metadata from participant
    # Pattern from: https://docs.livekit.io/agents/worker/job
    try:
        # Wait for first participant (the user who triggered agent dispatch)
        participant = await ctx.wait_for_participant()

        if participant.metadata:
            # ✅ VERIFIED: participant.metadata is a JSON string
            # Reference: https://docs.livekit.io/home/client/state/participant-attributes
            metadata = json.loads(participant.metadata)
            logger.info(f"Participant metadata: {metadata}")

            # Store email for use in agent
            agent.session_data['user_email'] = metadata.get('user_email', '')
            agent.session_data['user_metadata'] = metadata

            if agent.session_data['user_email']:
                logger.info(f"Session started for email: {agent.session_data['user_email']}")
        else:
            logger.info("No participant metadata available")

    except Exception as e:
        logger.warning(f"Could not extract participant metadata: {e}")
        # Graceful fallback - session continues without email

    # ... rest of existing code (session start, etc) ...
```

**Location 2**: Update analytics export to include email (line ~1020)

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
            logger.info(f"  - User email: {session_payload['user_email']}")
        logger.info(f"  - Duration: {session_payload['duration_seconds']:.1f}s")
        # ... rest of logging ...

        # Send to analytics queue
        await send_to_analytics_queue(session_payload)

    except Exception as e:
        logger.error(f"Failed to export session data: {e}", exc_info=True)

ctx.add_shutdown_callback(export_session_data)
```

---

## LiveKit SDK Verification

### ✅ Verified Patterns

1. **Token Metadata** (Node.js SDK)
   - Source: [Authentication Docs](https://docs.livekit.io/home/get-started/authentication.md)
   - Pattern: `new AccessToken(apiKey, secret, { identity, metadata: JSON.stringify(...) })`
   - Our implementation: Matches exactly

2. **Participant Metadata Access** (Python SDK)
   - Source: [Job Lifecycle Docs](https://docs.livekit.io/agents/worker/job)
   - Pattern: `participant = await ctx.wait_for_participant()` then `participant.metadata`
   - Our implementation: Matches exactly

3. **Metadata Format**
   - Source: [Participant Attributes Docs](https://docs.livekit.io/home/client/state/participant-attributes)
   - `participant.metadata` is a single string (we use JSON.stringify/parse)
   - Size limit: 64 KiB (our email metadata is ~100 bytes)
   - Our implementation: Within limits, proper JSON handling

### ✅ SDK Version Compatibility

**Frontend**:
- `livekit-client`: ^2.15.8 ✅
- `livekit-server-sdk`: ^2.13.2 ✅

**Backend (Python)**:
- LiveKit Agents: Latest ✅

All versions support participant metadata in tokens.

---

## Testing Instructions

### 1. Frontend Testing

```bash
cd frontend-ui/pandadoc-voice-ui
npm run dev
```

**Test steps**:
1. Open http://localhost:3000
2. Open DevTools → Network tab
3. Enter email: `test@company.com`
4. Click "Start Call"
5. Check `/api/connection-details` request body:
   ```json
   {
     "room_config": { "agents": [{ "agent_name": "..." }] },
     "user_email": "test@company.com"  // ✅ Should be present
   }
   ```

### 2. Backend Token Testing

**Decode the token**:
1. Copy `participantToken` from response
2. Go to https://jwt.io
3. Paste token
4. Verify decoded payload includes:
   ```json
   {
     "sub": "trialist_...",
     "metadata": "{\"user_email\":\"test@company.com\",\"session_start\":\"...\"}"
   }
   ```

### 3. Agent Testing

```bash
cd my-app
uv run python src/agent.py dev
```

**Check logs for**:
- `"Participant metadata: {'user_email': 'test@company.com', ...}"`
- `"Session started for email: test@company.com"`
- Analytics export includes `user_email` field

### 4. End-to-End Verification

```bash
# After a test call, check S3 for the session data
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ --recursive --region us-west-1

# Download and inspect a recent file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=29/[FILE].gz - \
  --region us-west-1 | gunzip | jq '.user_email'
```

Should output: `"test@company.com"`

---

## Common Issues & Solutions

### Issue: Email not in agent logs
**Solution**: Check that:
1. Frontend sessionStorage has `userFormData`
2. Backend request body includes `user_email`
3. Token JWT includes `metadata` field (use jwt.io)
4. Agent is waiting for participant: `await ctx.wait_for_participant()`

### Issue: "participant.metadata is None"
**Solution**: User may have connected before metadata was set. This is rare with agent dispatch but can happen. The code handles this gracefully with fallback.

### Issue: JSON parse error
**Solution**: Ensure metadata is JSON serialized in backend:
```typescript
metadata: JSON.stringify({ user_email: userEmail })  // Must be string
```

---

## Salesforce Integration

Once email flows through, use it to match Salesforce records:

### Simple Field Update (Recommended)

```python
from simple_salesforce import Salesforce

sf = Salesforce(username='...', password='...', security_token='...')

# Update Lead/Contact with session ID
sf.Lead.update_by_external_id(
    'Email',  # External ID field
    session_data['user_email'],  # Email value
    {
        'Last_Voice_Session__c': session_data['session_id'],
        'Last_Voice_Call_Date__c': session_data['end_time'],
        'Voice_Qualification_Tier__c': session_data['discovered_signals'].get('qualification_tier'),
    }
)
```

---

## Deployment Checklist

- [ ] Frontend changes deployed
- [ ] Backend token generation updated
- [ ] Python agent deployed with metadata extraction
- [ ] Test call completed with known email
- [ ] S3 data verified to include email
- [ ] Salesforce matching tested

---

## References

- **[LiveKit Authentication](https://docs.livekit.io/home/get-started/authentication.md)**: Token generation with metadata
- **[Participant Attributes](https://docs.livekit.io/home/client/state/participant-attributes.md)**: Metadata and attributes API
- **[Job Lifecycle](https://docs.livekit.io/agents/worker/job)**: Accessing participant data in agents
- **[LiveKit Agents Examples](https://github.com/livekit/agents/tree/main/examples)**: Official code examples

---

**Implementation Time**: 30-45 minutes
**Confidence Level**: ✅ High - Verified against official LiveKit SDK patterns

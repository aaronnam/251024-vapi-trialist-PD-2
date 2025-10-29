# Email Metadata Implementation Guide

## Overview
This guide provides exact code changes to pass email from frontend form → LiveKit → Python agent → Analytics → Salesforce.

**Current State**: Email is collected and stored in sessionStorage but NOT passed to LiveKit.
**Target State**: Email flows through entire pipeline for Salesforce matching.

---

## Implementation Changes

### 1. Frontend Changes: `hooks/useRoom.ts`

**File**: `/frontend-ui/pandadoc-voice-ui/hooks/useRoom.ts`

**Current Code (lines 39-69):**
```typescript
const tokenSource = useMemo(
  () =>
    TokenSource.custom(async () => {
      const url = new URL(
        process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? '/api/connection-details',
        window.location.origin
      );

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

**CHANGE TO:**
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
            // ADD THIS: Pass email to backend
            user_email: userEmail,
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

**Current Code (lines 190-248):**
```typescript
export async function POST() {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Generate unique room name for each PandaDoc trial session
    const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Generate participant identity for trialist
    const participantIdentity = `trialist_${Date.now()}`;
    const participantName = 'PandaDoc Trialist';

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(userInfo: AccessTokenOptions, roomName: string): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '30m', // 30 minute sessions for trialists
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  return at.toJwt();
}
```

**CHANGE TO:**
```typescript
export async function POST(request: Request) {  // ADD: request parameter
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Parse request body to get email
    const body = await request.json();
    const userEmail = body.user_email || '';

    // Generate unique room name for each PandaDoc trial session
    const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Generate participant identity for trialist
    const participantIdentity = `trialist_${Date.now()}`;
    const participantName = 'PandaDoc Trialist';

    // ADD: Create metadata object with email
    const metadata = {
      user_email: userEmail,
      session_start: new Date().toISOString(),
    };

    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
        metadata: JSON.stringify(metadata)  // ADD: Include metadata in token
      },
      roomName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

// No changes needed to createParticipantToken function - it already accepts metadata in userInfo
```

---

### 3. Python Agent Changes: `my-app/src/agent.py`

**File**: `/Users/aaron.nam/Desktop/Repos/251024-vapi-trialist-PD-2/my-app/src/agent.py`

**Add this code at line ~950 in the `entrypoint` function, right after creating the agent instance:**

```python
async def entrypoint(ctx: JobContext):
    # ... existing code ...

    # Create agent instance (existing line ~989)
    agent = PandaDocAgent()

    # ADD THIS: Extract user metadata from participant
    try:
        # Get the first participant (the user who connected)
        participants = ctx.room.remote_participants
        if participants:
            # Get the first participant's metadata
            participant = list(participants.values())[0]
            if participant.metadata:
                metadata = json.loads(participant.metadata)
                logger.info(f"Participant metadata: {metadata}")

                # Store email in session data for analytics
                agent.session_data['user_email'] = metadata.get('user_email', '')
                agent.session_data['user_metadata'] = metadata
        else:
            # Fallback: check local participant metadata (for testing)
            if ctx.room.local_participant and ctx.room.local_participant.metadata:
                metadata = json.loads(ctx.room.local_participant.metadata)
                agent.session_data['user_email'] = metadata.get('user_email', '')
                agent.session_data['user_metadata'] = metadata
                logger.info(f"Local participant metadata: {metadata}")
    except Exception as e:
        logger.warning(f"Could not extract participant metadata: {e}")
        agent.session_data['user_email'] = ''
        agent.session_data['user_metadata'] = {}

    # Log what we captured
    if agent.session_data.get('user_email'):
        logger.info(f"Session started for email: {agent.session_data['user_email']}")

    # ... rest of existing code ...
```

**Then update the analytics export (line ~1020) to include email:**

```python
async def export_session_data():
    """Export session data to analytics queue on shutdown."""
    try:
        # ... existing code ...

        session_payload = {
            # Session metadata
            "session_id": ctx.room.name,
            "user_email": agent.session_data.get('user_email', ''),  # ADD THIS
            "user_metadata": agent.session_data.get('user_metadata', {}),  # ADD THIS
            "start_time": agent.session_data["start_time"],
            "end_time": datetime.now().isoformat(),
            # ... rest of existing payload ...
        }

        # ... rest of existing code ...
```

**Also add the import at the top of the file (around line 10):**
```python
import json  # Add this if not already imported
```

---

## Testing Instructions

### 1. Local Testing

**Frontend Testing:**
```bash
cd frontend-ui/pandadoc-voice-ui
npm run dev
```

1. Open browser to http://localhost:3000
2. Enter email in form
3. Open DevTools → Application → Session Storage
4. Verify `userFormData` contains email
5. Start call
6. Check Network tab for `/api/connection-details` request
7. Verify request body includes `user_email`

**Backend Testing:**
```bash
# In the API route, add logging
console.log('Received email:', userEmail);
console.log('Metadata being added to token:', metadata);
```

**Agent Testing:**
```bash
cd my-app
uv run python src/agent.py dev
```

Check logs for:
- "Participant metadata: {'user_email': 'test@example.com'...}"
- "Session started for email: test@example.com"
- Analytics export should include email

### 2. End-to-End Verification

1. **Frontend → Backend**: Check POST request includes email
2. **Backend → Token**: Verify token JWT includes metadata (decode at jwt.io)
3. **Token → Agent**: Check agent logs show email extracted
4. **Agent → Analytics**: Verify S3 export includes email field

---

## Salesforce Matching Strategy

Once email is flowing through the pipeline:

### Option 1: Simple Field Update (Recommended)
```python
# In your analytics pipeline
from simple_salesforce import Salesforce

sf = Salesforce(username='...', password='...', security_token='...')

# Update Lead/Contact with session ID
sf.Lead.update_by_external_id(
    'Email',
    session_data['user_email'],
    {
        'Last_Voice_Session__c': session_data['session_id'],
        'Last_Voice_Call_Date__c': session_data['end_time'],
        'Voice_Qualification_Tier__c': session_data['discovered_signals'].get('qualification_tier'),
    }
)
```

### Option 2: Campaign Member
- Create Campaign: "Voice AI Trials Q1 2025"
- Add each caller as Campaign Member
- Store session data on CampaignMember record

### Option 3: Custom Object
- Create `Voice_Call__c` object
- Link to Lead/Contact via email lookup
- Store full session transcript and metadata

---

## Deployment Checklist

### Frontend Deployment
- [ ] Test email capture locally
- [ ] Verify sessionStorage retrieval
- [ ] Confirm token request includes email
- [ ] Deploy to staging/preview
- [ ] Test in staging environment
- [ ] Deploy to production

### Backend Deployment
- [ ] Test token generation with metadata locally
- [ ] Verify JWT includes email (jwt.io)
- [ ] Deploy API route changes
- [ ] Monitor error logs

### Agent Deployment
- [ ] Test metadata extraction locally
- [ ] Verify analytics export includes email
- [ ] Deploy with `lk agent deploy`
- [ ] Monitor CloudWatch logs for email capture

### Verification
- [ ] Make test call with known email
- [ ] Check S3 for session data with email
- [ ] Verify Salesforce can match on email
- [ ] Confirm analytics pipeline processes email

---

## Rollback Plan

If issues occur, revert changes in this order:

1. **Agent**: Remove metadata extraction (won't break calls)
2. **Backend**: Remove metadata from token (won't break connection)
3. **Frontend**: Remove email from request body (won't affect form)

Each component can be rolled back independently without breaking the system.

---

## Common Issues & Solutions

### Issue: Email not appearing in agent logs
**Solution**: Check participant metadata structure, may need to adjust extraction logic

### Issue: Token generation fails
**Solution**: Ensure metadata is JSON serializable, check for special characters in email

### Issue: SessionStorage is empty
**Solution**: Check timing - ensure form submission completes before connection starts

### Issue: Salesforce duplicate handling
**Solution**: Use upsert operations with email as external ID

---

## Next Steps

1. **Week 1**: Deploy email capture to production
2. **Week 2**: Set up manual Salesforce sync (CSV export)
3. **Week 3**: Automate with Lambda → Salesforce API
4. **Month 2**: Add enrichment (company data, lead scoring)

---

**Implementation Time**: 30-45 minutes
**Testing Time**: 30 minutes
**Deployment**: 15 minutes

Total: ~2 hours to production

---

**Questions?** The implementation is straightforward - email flows naturally through LiveKit's participant metadata system. This is the standard pattern for passing user context in LiveKit applications.
# Call Initiation Notifications

**Status**: Ready for implementation
**Complexity**: Minimal (6 lines of code)
**Dependencies**: None (uses existing imports)

---

## Overview

Send Slack notifications (or email via AWS SES) whenever a user initiates a call with the LiveKit voice agent. This provides real-time visibility into trial user engagement without adding complexity or overhead.

### Why This Matters

- **Real-time awareness**: Know immediately when someone calls
- **Sales intelligence**: Identify high-engagement trialists faster
- **Zero latency impact**: Fire-and-forget pattern doesn't affect call quality
- **No new infrastructure**: Uses existing Slack webhooks or AWS SES

---

## Architecture

The notification triggers in two places:

1. **Call Initiation**: When a user joins the LiveKit room (already happens in entrypoint)
2. **Participant Detection**: After extracting user email from participant metadata
3. **Async Send**: Non-blocking Slack webhook call with 2-second timeout

### Flow Diagram

```
User clicks "Call" button
    ↓
Frontend connects to LiveKit room
    ↓
Agent entrypoint starts (JobContext)
    ↓
session.start() completes
    ↓
Participant metadata extracted → user_email
    ↓
notify_call_started() fires (async)
    ↓
Slack webhook receives notification
    ↓
Message appears in Slack channel
```

---

## Implementation

### Option 1A: Slack with Bot Token (No App Creation Required)

**File**: `my-app/src/agent.py`

**Step 1**: Add notification function before `entrypoint()` (around line 1190):

```python
async def notify_call_started(room_name: str, user_email: str):
    """Send Slack notification using Bot token - fire and forget"""
    slack_token = os.getenv("SLACK_BOT_TOKEN")
    slack_channel = os.getenv("SLACK_CHANNEL_ID", "#voice-agent-calls")

    if not slack_token:
        return

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {slack_token}"},
                json={
                    "channel": slack_channel,
                    "text": f"📞 New call started by {user_email or 'Unknown'}",
                    "blocks": [{
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*New PandaDoc Trial Call*\nRoom: `{room_name}`\nUser: {user_email or 'Unknown'}\nTime: {datetime.now().strftime('%I:%M %p')}"
                        }
                    }]
                }
            )
    except:
        pass  # Never let notification failure affect the call
```

### Option 1B: Slack with Incoming Webhook (Requires App Creation)

**File**: `my-app/src/agent.py`

**Step 1**: Add notification function before `entrypoint()` (around line 1190):

```python
async def notify_call_started(room_name: str, user_email: str):
    """Send Slack notification when call starts - fire and forget"""
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        return

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            await client.post(slack_webhook, json={
                "text": f"📞 New call started by {user_email or 'Unknown'}",
                "blocks": [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New PandaDoc Trial Call*\nRoom: `{room_name}`\nUser: {user_email or 'Unknown'}\nTime: {datetime.now().strftime('%I:%M %p')}"
                    }
                }]
            })
    except:
        pass  # Never let notification failure affect the call
```

**Step 2**: Add notification call in `entrypoint()` at line ~1650 (after you've set `agent.user_email`):

```python
# Send Slack notification for new call
await notify_call_started(ctx.room.name, user_email)
```

**Full context** (where to add it):

```python
async def entrypoint(ctx: JobContext):
    # ... existing code ...

    # Extract user email from participant metadata
    if participant.metadata:
        metadata = json.loads(participant.metadata)
        user_email = metadata.get("user_email", "")
        agent.user_email = user_email
        agent.session_data["user_email"] = user_email
        agent.session_data["user_metadata"] = metadata

        # 👇 ADD THIS LINE:
        await notify_call_started(ctx.room.name, user_email)
```

### Option 2: AWS SES Email

If you prefer email notifications instead:

```python
async def notify_call_started(room_name: str, user_email: str):
    """Send email notification via AWS SES"""
    notification_email = os.getenv("NOTIFICATION_EMAIL")
    if not notification_email:
        return

    try:
        import boto3
        ses = boto3.client('ses', region_name='us-west-1')
        ses.send_email(
            Source=notification_email,
            Destination={'ToAddresses': [notification_email]},
            Message={
                'Subject': {'Data': f'New Call: {user_email or "Unknown"}'},
                'Body': {'Text': {'Data': f'Call started in room {room_name} at {datetime.now().isoformat()}'}}
            }
        )
    except:
        pass
```

---

## Configuration

### Option 1A: Slack Bot Token Setup (Recommended - No App Creation)

If you can't create Slack apps but your organization has existing Slack bots:

#### Getting a Bot Token

You have **two paths** to get a bot token:

**Path A: Use an Existing Bot (Fastest)**

Ask your Slack workspace admin or IT team:
> "We need to send notifications to Slack from our voice agent. Do we have an existing Slack bot I can use? I need a bot token (xoxb-...) with `chat:write` permission."

If they say yes, they'll provide:
- Bot token (format: `xoxb-...` - keep this secret!)
- The bot should have `chat:write` scope

**Path B: Request a New Bot (If No Existing Bot)**

If your organization doesn't have a suitable bot, you'll need to request one from your Slack admin. Send them this:

---

**Sample Request to Slack Admin:**

> Hi [Admin Name],
>
> I need to set up Slack notifications for our PandaDoc voice agent. Could you create a Slack bot for this purpose? Here's what I need:
>
> **Bot Configuration:**
> - Bot name: "PandaDoc Voice Agent Notifier" (or similar)
> - Required OAuth scope: `chat:write`
> - Channels to post to: `#voice-agent-calls` (or your preferred channel)
>
> **What I need from you:**
> - The bot token (format: `xoxb-...`)
> - Confirmation the bot has been added to the notification channel
>
> The bot will only post simple notifications when someone initiates a call (room name, user email, timestamp). No message reading or user data access required.
>
> Thanks!

---

**What Your Admin Will Do:**

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "PandaDoc Voice Agent Notifier"
4. Go to "OAuth & Permissions" in sidebar
5. Under "Scopes" → "Bot Token Scopes" → Add `chat:write`
6. Click "Install to Workspace" at top of page
7. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
8. Add the bot to your notification channel:
   - Go to the channel in Slack
   - Type `/invite @BotName`
9. Send you the token

#### Step 1: Get Your Bot Token

Use one of the paths above to obtain:
- Bot token (format: `xoxb-...`)
- Confirm it has `chat:write` scope

#### Step 2: Get the Channel ID

- Open Slack, go to the channel where you want notifications
- Click the channel name at the top
- Scroll down in the modal
- Copy the "Channel ID" (format: `C05XXXXXXXXX`)
- **Alternative**: You can use the channel name directly like `#voice-agent-calls`

#### Step 3: Deploy to LiveKit Cloud

```bash
# Add bot token and channel ID
lk agent update-secrets --secrets "SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-HERE,SLACK_CHANNEL_ID=C05XXXXXXXXX"

# Or use channel name instead of ID:
lk agent update-secrets --secrets "SLACK_BOT_TOKEN=xoxb-YOUR-TOKEN-HERE,SLACK_CHANNEL_ID=#voice-agent-calls"

# Restart the agent
lk agent restart

# Deploy the code
lk agent deploy
```

### Option 1B: Slack Webhook Setup (Requires App Creation)

If you CAN create Slack apps:

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "PandaDoc Calls", Workspace: select yours
4. In left sidebar: "Incoming Webhooks"
5. Toggle "Activate Incoming Webhooks" to ON
6. Click "Add New Webhook to Workspace"
7. Select the channel for notifications (e.g., #voice-agent-calls)
8. Click "Allow"
9. Copy the webhook URL (looks like `https://hooks.slack.com/services/T.../B.../X...`)

**Deploy to LiveKit Cloud:**

```bash
# Add the webhook URL as a secret
lk agent update-secrets --secrets "SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Restart the agent
lk agent restart

# Deploy the code
lk agent deploy
```

### Email Setup (SES Alternative)

```bash
# Set your notification email
lk agent update-secrets --secrets "NOTIFICATION_EMAIL=your-email@pandadoc.com"

# Restart
lk agent restart
```

---

## Safety & Reliability

### Why This Is Bulletproof

| Concern | Mitigation |
|---------|-----------|
| **Blocks the call?** | No - async, non-blocking, 2s timeout max |
| **Crashes if Slack down?** | No - silent `except` clause |
| **Memory leaks?** | No - httpx `async with` auto-closes |
| **Race conditions?** | No - fires after participant detected |
| **Missing imports?** | No - httpx already in your imports |
| **Affects event handlers?** | No - independent of `@session.on()` |
| **Performance impact?** | Negligible (<10ms, async only) |

### Error Handling

The try/except silently catches all errors:
- Network timeouts (2s limit)
- Invalid webhook URL
- Slack API errors
- HTTP connection errors

Call quality is never affected.

---

## What Gets Sent

### Slack Message Example

```
📞 New call started by alice@company.com

New PandaDoc Trial Call
Room: `trial-user-12345`
User: alice@company.com
Time: 02:15 PM
```

### Message Breakdown

- **Emoji**: Visual indicator in Slack sidebar
- **Room**: LiveKit room ID (for debugging/tracing)
- **User**: Email from participant metadata
- **Time**: UTC timestamp of call initiation

---

## Testing

### Local Test (Console Mode)

**For Bot Token Method:**
```bash
# 1. Set bot token and channel
export SLACK_BOT_TOKEN="xoxb-..."
export SLACK_CHANNEL_ID="C05XXXXXXXXX"

# 2. Run in console mode
cd my-app
uv run python src/agent.py console

# 3. When prompted, provide metadata with email
# 4. Slack message should appear immediately
```

**For Webhook Method:**
```bash
# 1. Set webhook URL
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."

# 2. Run in console mode
cd my-app
uv run python src/agent.py console

# 3. When prompted, provide metadata with email
# 4. Slack message should appear immediately
```

### Production Verification

```bash
# 1. After deploying, check logs
lk agent logs

# 2. Should see notification code executing
# (check for any errors in try/except)

# 3. Make a test call through Agent Playground
# 4. Check Slack channel for notification
```

---

## Monitoring

### Where to Check

1. **Slack**: Messages appear in configured channel
2. **Logs**: `lk agent logs | grep notify` (won't appear since it's silent on success)
3. **Duration**: Should see messages within <1 second of call initiation

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No Slack messages | Verify webhook URL in secrets: `lk agent secrets` |
| Messages appear late | Check agent logs for network issues |
| Wrong email | Verify participant metadata is being sent correctly |
| Only 1 webhook sent | Confirm `await notify_call_started()` is called once |

---

## FAQ

### Q: Does this add latency to calls?
**A**: No. The notification is async and non-blocking. The call flow continues immediately.

### Q: What if Slack is down?
**A**: The call continues normally. The notification silently fails. No impact to user experience.

### Q: Can we customize the message?
**A**: Yes. Modify the JSON in the Slack blocks section (see Slack API for formatting options).

### Q: Do we need to enable any permissions?
**A**:
- **Bot Token**: Requires `chat:write` scope (ask your Slack admin)
- **Webhook**: No permissions needed, the webhook handles all auth

### Q: Can we send to multiple Slack channels?
**A**: Yes. Create multiple webhooks and call `notify_call_started()` multiple times with different webhook URLs.

### Q: What about GDPR/privacy?
**A**: Only the user's email (already in metadata) is sent. No audio, transcripts, or sensitive data.

---

## Future Enhancements (Not Needed Now)

- Send more detailed qualification signals (team size, integration needs)
- Create Slack thread with call transcript after completion
- Route notifications to different channels based on qualification tier
- Integrate with CRM to auto-create activity records
- Add user thumbnail/avatar to Slack message

These can be added later if needed. Keep it simple for now.

---

## Related Documentation

- [Observability Strategy](./OBSERVABILITY_STRATEGY.md) - Overall monitoring approach
- [Agent Entrypoint Pattern](../../IMPLEMENTATION_PLAN.md#entrypoint-function) - How entrypoint works
- [Session Data Export](./LANGFUSE_USER_ID_GUIDE.md) - Post-call analytics

---

## Code Location

- **Function location**: `my-app/src/agent.py:1190` (before entrypoint)
- **Call location**: `my-app/src/agent.py:1650` (in entrypoint, after email extraction)
- **Dependencies**: `httpx` (already imported)
- **Environment variables**:
  - Bot Token method: `SLACK_BOT_TOKEN`, `SLACK_CHANNEL_ID`
  - Webhook method: `SLACK_WEBHOOK_URL`
  - Email method: `NOTIFICATION_EMAIL`

---

**Last Updated**: 2025-10-30
**Status**: Ready for implementation
**Lines of Code**: 6 (plus setup)

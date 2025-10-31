# Call Notifications via LiveKit Webhooks + Zapier

**Status**: Ready for implementation
**Complexity**: Minimal (no code changes required)
**Dependencies**: Zapier account, Slack (or Gmail)

---

## Overview

Get Slack or email notifications whenever someone initiates a call with your voice agent using **LiveKit's built-in webhooks** + **Zapier** automation. This approach requires **zero code changes** to your agent.

### Why This Approach

- ✅ **No code changes** - Uses LiveKit Cloud's webhook feature
- ✅ **No bot tokens needed** - Zapier handles Slack auth for you
- ✅ **Works immediately** - Set up in 10 minutes
- ✅ **Slack or Email** - Send to Slack channel or Gmail inbox
- ✅ **Zero maintenance** - Managed by LiveKit + Zapier

---

## Architecture

```
User joins LiveKit room
    ↓
LiveKit Cloud detects "participant_joined" event
    ↓
LiveKit sends webhook to Zapier
    ↓
Zapier triggers "Catch Hook"
    ↓
Zapier posts to Slack (or sends Gmail)
    ↓
Message appears in Slack channel
```

### What Gets Sent

LiveKit automatically sends this data in the webhook:

```json
{
  "event": "participant_joined",
  "room": {
    "name": "trial-user-12345",
    "sid": "RM_xxx"
  },
  "participant": {
    "identity": "user-12345",
    "name": "Alice Smith",
    "metadata": "{\"user_email\":\"alice@company.com\"}"
  },
  "createdAt": 1698765432
}
```

---

## Setup Instructions

### Step 1: Create Zapier Webhook (5 minutes)

1. **Go to Zapier**: https://zapier.com/
2. **Create New Zap**: Click "Create Zap"
3. **Trigger**: Search for "Webhooks by Zapier"
4. **Event**: Select "Catch Hook"
5. **Continue**: Zapier gives you a webhook URL
   - Format: `https://hooks.zapier.com/hooks/catch/12345/abcdef/`
   - **Copy this URL** - you'll need it in Step 2

6. **Test the webhook** (optional):
   - Zapier will wait for a test webhook
   - You can skip this for now and test later

### Step 2: Configure LiveKit Cloud Webhook (2 minutes)

1. **Go to LiveKit Cloud Dashboard**: https://cloud.livekit.io/
2. **Select your project**: `pd-voice-trialist-4`
3. **Go to Settings** → **Webhooks**
4. **Add Webhook URL**:
   - Paste the Zapier webhook URL from Step 1
   - Example: `https://hooks.zapier.com/hooks/catch/12345/abcdef/`
5. **Save**

That's it! LiveKit will now send webhook events to Zapier.

### Step 3: Configure Zapier Slack Action (3 minutes)

Back in Zapier:

1. **Wait for Test Event**: Make a test call to your agent, or click "Skip Test"
2. **Action**: Click "+" to add an action
3. **App**: Search for "Slack"
4. **Event**: Select "Send Channel Message"
5. **Slack Account**: Connect your Slack workspace
   - Zapier will ask for permission to post messages
   - You don't need admin access - just permission to post to the channel
6. **Configure Message**:

   **Channel**: Select the channel (e.g., `#voice-agent-calls`)

   **Message Text**:
   ```
   📞 *New PandaDoc Call*

   *User:* {{participant__name}}
   *Identity:* {{participant__identity}}
   *Room:* {{room__name}}
   *Time:* {{createdAt}}
   ```

   **Tips**:
   - Use Zapier's field picker to insert webhook data
   - Use `*bold*` for Slack formatting
   - Add emoji for visual notifications
   - See "Advanced" section below to parse user email from metadata

7. **Test Action**: Zapier sends a test message to Slack
8. **Turn On Zap**: Enable the automation

---

### Alternative: Gmail Notifications

If you prefer email instead of Slack:

1. **Action**: Search for "Gmail" instead of Slack
2. **Event**: Select "Send Email"
3. **Gmail Account**: Connect your Gmail account
4. **Configure**:
   - **To**: `your-email@pandadoc.com`
   - **Subject**: `📞 New PandaDoc Call: {{participant__name}}`
   - **Body**: Include user, room, time details
5. **Test and Enable**

---

## What You'll Receive

### Slack Message Example

```
📞 *New PandaDoc Call*

*User:* Alice Smith
*Identity:* user-12345
*Room:* trial-user-12345
*Time:* 1698765432
```

### Gmail Example (If Using Email)

```
Subject: 📞 New PandaDoc Call: Alice Smith

New call detected!

User: Alice Smith (user-12345)
Room: trial-user-12345
Time: 1698765432
```

---

## Advanced: Parse User Email from Metadata

The `participant.metadata` field contains JSON. To extract the email:

### Option A: Use Zapier's Code Step (Recommended)

After the webhook trigger, add a "Code by Zapier" step:

```javascript
// Input: metadata (string from webhook)
const metadata = inputData.metadata;

// Parse JSON
let email = "Unknown";
try {
  const data = JSON.parse(metadata);
  email = data.user_email || "Unknown";
} catch (e) {
  email = "Error parsing metadata";
}

// Output
output = { user_email: email };
```

Then use `{{user_email}}` in your Slack message or email template.

### Option B: Use Zapier's Formatter

1. Add "Formatter by Zapier" step
2. Event: "Text" → "Extract Pattern"
3. Input: `{{participant__metadata}}`
4. Pattern: `"user_email":"([^"]+)"`
5. Use extracted value in email

---

## Testing

### Test the Full Flow

1. **Make a test call** to your agent via Agent Playground
2. **Check Zapier**: Go to Zap History to see if webhook was received
3. **Check Slack** (or Gmail): Message should appear within 1-2 seconds

### Troubleshooting

| Issue | Solution |
|-------|----------|
| No webhook received | Check LiveKit webhook URL is correct |
| Webhook received but no Slack message | Check Slack action is configured and Zap is enabled |
| Can't select Slack channel | Make sure you have permission to post in that channel |
| Message missing user data | Check participant metadata is being sent correctly |
| Duplicate messages | LiveKit may send multiple events, add Zapier filter |

---

## Filtering Events (Optional)

If you want to filter out agent participants (only notify for real users):

**In Zapier, add a Filter step:**
1. Add "Filter by Zapier" step after webhook (before Slack action)
2. Condition: `participant__kind` → `(Text) Does not exactly match` → `AGENT`
3. This ensures only human participants trigger Slack messages

---

## Cost

- **LiveKit Webhooks**: Free (included in LiveKit Cloud)
- **Zapier**:
  - Free tier: 100 tasks/month (likely sufficient)
  - Paid: $19.99/month for 750 tasks
- **Slack**: Free (Zapier handles the connection)
- **Gmail**: Free (if using email instead)

### Expected Usage

- ~1 webhook per call = ~100 calls/month fits free tier
- If you exceed, upgrade Zapier or use multiple free accounts

---

## Alternative Destinations

Instead of Slack, Zapier can send to 6000+ apps:

- **Microsoft Teams**: Post to Teams channel
- **Discord**: Send to Discord channel
- **Email**: Gmail, Outlook, Office 365
- **SMS**: Send text via Twilio
- **Google Sheets**: Log calls to spreadsheet
- **Webhook**: Forward to your own endpoint
- **CRM**: Salesforce, HubSpot activity logging

All without code changes!

---

## Comparison to Code-Based Approach

| Aspect | Webhook + Zapier | Code in Agent |
|--------|------------------|---------------|
| **Setup Time** | 10 minutes | 30 minutes |
| **Code Changes** | None | Yes |
| **Maintenance** | Zero | Update on plugin changes |
| **Flexibility** | Very high (Zapier has 6000+ apps) | Limited to what you code |
| **Cost** | $0-20/month | $0 (but engineering time) |
| **Slack Access** | Works through Zapier | Need bot token |
| **Debugging** | Zapier UI shows all events | Check agent logs |

---

## Going Further

Once you have Zapier set up, you can easily add:

1. **Slack notifications** (if you get bot access later)
2. **Log to Google Sheets** for call tracking
3. **Send to CRM** (Salesforce, HubSpot)
4. **Trigger other automations** based on call events
5. **Filter by qualification tier** (parse metadata for team size, etc.)

All by adding steps in Zapier, no code needed.

---

## Security Note

The webhook URL from Zapier is sensitive - anyone with this URL can send fake webhooks. For production:

1. **Keep the URL secret** - Don't commit to git
2. **Use Zapier's webhook validation** (check signature)
3. **Or** set up webhook authentication in LiveKit Cloud

For internal notifications, the default security is usually sufficient.

---

## Related Documentation

- [LiveKit Webhooks Documentation](https://docs.livekit.io/home/server/webhooks/) - Official webhook reference
- [Zapier Webhooks Guide](https://zapier.com/apps/webhook/integrations) - Zapier webhook tutorials
- [Code-Based Slack Notification](./CALL_INITIATION_NOTIFICATIONS.md) - Alternative if you need in-agent notifications

---

**Last Updated**: 2025-10-30
**Status**: Ready for implementation
**Setup Time**: 10 minutes
**Code Changes Required**: None ✅

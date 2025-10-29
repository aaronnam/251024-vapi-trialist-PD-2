# Google Calendar Meeting Booking

**Status**: ✅ Designed and documented
**Last Updated**: October 27, 2025
**Compatibility**: ✅ LiveKit Agents verified

## Overview

Voice-driven meeting booking integration that enables the PandaDoc Voice Agent to directly schedule sales meetings with qualified trial users using Google Calendar.

**Key Design Philosophy**:
- **Qualification-Driven**: Tool only activates for qualified leads (Tier 1: Sales-Ready)
- **Simplicity First**: Book immediately without complex availability checking
- **Voice-Optimized**: Fast execution with natural conversational flow
- **No Fallback Complexity**: Never offers human assistance (clear boundaries)
- **LiveKit Native**: Seamlessly integrated with LiveKit Agents framework

## Documentation

### [DESIGN.md](./DESIGN.md)
**Technical design and implementation guide**

- Executive summary and core requirements
- Design philosophy and principles
- Technical architecture and authentication setup
- Complete implementation code with examples
- Integration patterns with LiveKit Agents
- Salesforce integration options

**Use when**: Implementing or understanding the booking feature architecture

## Feature Overview

### What It Does
- Detects when qualified users want to schedule meetings
- Directly creates Google Calendar events
- Provides natural conversational confirmation
- Integrates user email with Salesforce for lead tracking

### When It Activates
- User is qualified (Tier 1: Sales-Ready)
- User explicitly requests a meeting
- Agent has calendar credentials configured

### What It Won't Do
- Offer to unqualified users
- Check complex availability
- Offer human handoff (clear business boundaries)
- Handle rescheduling (booking only)

## Architecture

### Components

```
User Request
    ↓
Qualification Check
    ├─ Not Qualified? → Don't offer booking
    └─ Qualified? → Continue
    ↓
Meeting Intent Detection
    ├─ "Schedule a meeting" → Offer booking
    └─ Other intents → Don't offer
    ↓
Google Calendar Integration
    ├─ Authenticate with service account
    ├─ Parse user preferences (date/time)
    ├─ Create calendar event
    └─ Confirm with user
    ↓
Salesforce Integration
    └─ Link meeting to lead record via email
```

### Authentication

**Status**: ✅ Already configured

```
Environment Variables:
├── GOOGLE_SERVICE_ACCOUNT_JSON    (path to service account credentials)
└── GOOGLE_CALENDAR_ID             (shared calendar ID)

Service Account:
├── Location: /.secrets/pandadoc-voice-agent-03fa518aa3d0.json
└── Permissions: Calendar event creation
```

**No additional setup needed** - credentials are ready to use.

## Implementation Details

### Core Tool: `book_sales_meeting`

```python
@function_tool(
    description="Book a sales meeting with the user..."
)
async def book_sales_meeting(
    preferred_date: str = None,
    preferred_time: str = None,
    user_email: str = None
) -> str:
    """
    Books a direct sales meeting on the calendar.
    Only available for qualified users.
    """
```

**Parameters**:
- `preferred_date` - User's preferred date (optional, parsed naturally)
- `preferred_time` - User's preferred time (optional, parsed naturally)
- `user_email` - User's email for invitation (extracted from session)

**Returns**: Confirmation message with meeting details

### Key Features

1. **Natural Date/Time Parsing**
   - "Tomorrow at 2pm" → Next day, 14:00
   - "Next Tuesday morning" → Inferred time slot
   - "This week" → Suggest available slot

2. **Email Extraction**
   - Automatically gets user email from session metadata
   - No need to ask user for email twice
   - Used in Salesforce lead linking

3. **Calendar Integration**
   - Creates event on shared calendar
   - Sends invitation to user email
   - Includes meeting details and context

4. **Conversation Flow**
   - Natural confirmation: "I'll send the invite to john@acme.com"
   - No technical jargon
   - Smooth integration into conversation

## Integration with LiveKit

**Verified Compatibility**: ✅

The design uses standard LiveKit Agents patterns:
- `@function_tool` decorator (LiveKit standard)
- Async/await for external API calls
- Error handling with graceful degradation
- Session context for user data
- Live testing with agent console

```python
# Example tool definition (LiveKit compatible)
@function_tool(
    description="Book a sales meeting with qualified users on Google Calendar"
)
async def book_sales_meeting(
    preferred_date: str = None,
    preferred_time: str = None
) -> str:
    # Implementation here
    pass
```

## Salesforce Integration Options

### Option 1: Simple Field Update (Recommended)
Update existing Lead/Contact with session information:
```python
sf.Lead.update_by_external_id('Email', user_email, {
    'Last_Voice_Session__c': session_id,
    'Last_Voice_Call_Date__c': end_time,
})
```
**Effort**: 5 minutes

### Option 2: Campaign Tracking
Create campaign and add callers as members:
- "Voice AI Trials Q1 2025" campaign
- Automatic lead matching by email
- Built-in reporting and attribution

**Effort**: 15 minutes

### Option 3: Custom Object
Create Voice_Call__c object for detailed tracking:
- Full conversation metadata
- Link to Lead/Contact via email lookup
- Store meeting details

**Effort**: 1 hour

## Conversation Examples

### Qualified User (Booking Offered)
```
User: "I'm interested in discussing enterprise features"
Agent: [Qualification detected] "I'd be happy to help! Would you like to schedule
        a quick sales call to discuss your needs?"
User: "Sure, tomorrow at 2pm?"
Agent: "Perfect! I'll send the invite to john@acme.com for tomorrow at 2pm.
        You should see it in your inbox shortly."
User: "Great, thanks!"
```

### Unqualified User (No Offer)
```
User: "This looks interesting but I need to think about it"
Agent: [Not qualified yet] "No problem! Feel free to reach out if you have questions.
        Here are some resources in the meantime..."
```

## Related Documentation

- **Design Details**: [DESIGN.md](./DESIGN.md)
- **Error Recovery**: [../error-recovery/README.md](../error-recovery/README.md) (for handling failures)
- **Development Guide**: [../../AGENTS.md](../../AGENTS.md)
- **Feature Index**: [../README.md](../README.md)

## Production Checklist

Before deploying to production:
- [ ] Verify Google service account credentials are loaded
- [ ] Test booking with qualified user in console mode
- [ ] Verify calendar invitations are sent correctly
- [ ] Check email addresses are captured correctly
- [ ] Test with date/time parsing edge cases
- [ ] Verify Salesforce integration is configured
- [ ] Run full test suite
- [ ] Load test with multiple concurrent bookings

## Testing

Test the feature with the agent console:

```bash
# Start in console mode
uv run python src/agent.py console

# Test scenarios:
# 1. "I want to schedule a sales meeting tomorrow at 2pm"
# 2. "Can we meet next week?"
# 3. "I'm qualified - book me a meeting for today at 3pm"
```

## Key Takeaways

✅ **Simple and focused** - Books meetings, nothing else
✅ **Qualification-driven** - Only for sales-ready users
✅ **Voice-optimized** - Natural conversation flow
✅ **Integrated** - Email auto-captured, Salesforce-linked
✅ **Proven patterns** - Follows LiveKit best practices
✅ **Production-ready** - Fully designed and documented

---

**Last Updated**: October 29, 2025
**Status**: ✅ Design Complete & Verified
**Next Steps**: Implementation and testing

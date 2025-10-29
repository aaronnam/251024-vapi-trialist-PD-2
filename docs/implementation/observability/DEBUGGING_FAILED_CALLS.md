# Debugging Failed Calls - Complete Workflow

**Last Updated**: 2025-10-29
**Time to Debug**: 2-5 minutes per call
**Tools**: Langfuse (traces), CloudWatch Logs (events), CloudWatch Alarms (alerts)

---

## How You'll Know a Call Failed

### 1. Real-Time Notifications (First Alert)

You'll get **automatic SNS email alerts** if error rate spikes:

```
Subject: ALARM: VoiceAgent-HighErrorRate

State Change: INSUFFICIENT_DATA → ALARM
Error Count exceeded threshold (>10 errors in 5 minutes)
Timestamp: 2025-10-29 20:15:00 UTC
Region: us-west-1
```

**What to do when alert arrives:**
1. Check CloudWatch dashboard for error rate pattern
2. Look at recent errors in dashboard widget
3. Get session IDs from dashboard or CloudWatch Logs
4. Jump to step 3 below (Find in Langfuse)

### 2. Dashboard Alert (Manual Check)

Open your **[CloudWatch Dashboard](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance)** during your day:

**Look for:**
- ❌ **Error Rate (1min)** widget showing spike
- ❌ **Recent Errors (Last 10)** widget showing error messages
- ❌ **Slow Sessions (>2s latency)** showing pattern

Each error in the dashboard has a **session ID** - this is your key to debugging.

### 3. User Complaint (Reactive Detection)

User says: _"My call didn't work"_

**Get the session ID from them:**
- Check LiveKit Cloud agent logs for their call time
- Or have them save the session ID when call ends
- Or ask: "What time did you call?" and search logs by timestamp

---

## Step-by-Step Debugging Workflow

### Phase 1: Identify the Session (1 minute)

#### Option A: From Dashboard Alert
```
Session ID appears in:
- "Recent Errors" widget
- "Slow Sessions" widget
Example: CAW_3Y7MVDtgE8xm
```

#### Option B: From User Complaint
```bash
# Search logs by approximate time
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --start-time $(date -u -d '30 minutes ago' +%s)000 \
  --filter-pattern "ERROR" \
  --region us-west-1 \
  --query 'events[*].[timestamp,message]' \
  --output table | head -20
```

#### Option C: From Error Rate Spike
Use CloudWatch Insights query: **"Voice Agent - Recent Errors"**
- Shows last 10 errors with session IDs
- Can sort by timestamp
- Click on session ID to filter

---

### Phase 2: Get Full Trace in Langfuse (2 minutes)

**This is the most important step** - traces show you EXACTLY what happened.

#### Step 1: Open Langfuse
Go to **[https://us.cloud.langfuse.com](https://us.cloud.langfuse.com)**

#### Step 2: Filter by Session ID
1. Click **"Traces"** in left sidebar
2. In the filter bar, search for session ID: `CAW_3Y7MVDtgE8xm`
3. Click on the trace to open

#### Step 3: Read the Trace Timeline

The trace shows every step of the conversation:

```
Timeline (read top to bottom):
├── Session Started
│   └── 2025-10-29 20:10:30
├── STT Processing (Speech-to-Text)
│   └── Duration: 0.45s ✅
│   └── Transcription: "Hello, I'm interested in..."
├── LLM Processing (Claude reasoning)
│   └── Duration: 0.87s ✅
│   └── Tokens: 142 input, 45 output
│   └── Reasoning: [full model response visible]
├── Tool Execution (Calendar booking, CRM lookup, etc.)
│   └── Calendar Query: FAILED ❌
│   └── Error: "Google Calendar API rate limited"
│   └── Retry: Attempted 2 times, still failed
├── TTS Processing (Text-to-Speech)
│   └── Status: Skipped (due to tool failure)
└── Session Ended
    └── Error State: true
    └── Final Message: "Unable to complete..."
```

---

### Phase 3: Identify Root Cause (2 minutes)

**Look for the first ❌ in the trace:**

#### Scenario 1: STT Failed
```
STT Processing: FAILED
Error: "No audio detected"
Possible causes:
- Caller had microphone issue
- Network packet loss during audio upload
- Audio encoding problem

Action: Ask user to retry with better audio
```

#### Scenario 2: LLM Failed
```
LLM Processing: FAILED
Error: "API rate limit exceeded - OpenAI quota"
Duration: 15.2s (timeout)

Possible causes:
- OpenAI API quota exhausted
- Network timeout
- Invalid prompt causing model error

Action: Check OpenAI billing, restart agent if needed
```

#### Scenario 3: Tool Failed (Most Common)
```
Tool Execution: Calendar Query
Error: "Google Calendar API unauthorized"
Tokens spent: 45 (partial LLM response)

Possible causes:
- Google service account token expired
- Insufficient scopes/permissions
- Calendar ID misconfigured

Action: Regenerate Google service account credentials
```

#### Scenario 4: TTS Failed
```
TTS Processing: FAILED
Error: "Cartesia API timeout"
Duration: 3.2s (exceeded threshold)

Possible causes:
- TTS service overloaded
- Network latency
- Text too long to convert

Action: Check TTS service status, simplify response
```

#### Scenario 5: Latency Timeout
```
Total Duration: 5.8s (exceeded max)
Breakdown:
- STT: 0.45s ✅
- LLM: 2.3s ✅
- Tool: 2.8s ⚠️ (slow)
- TTS: 0.3s ✅

Possible causes:
- Tool (Calendar/CRM) query too slow
- Database lookup hanging
- Third-party API slow response

Action: Optimize tool queries, add timeouts
```

---

## Real Example: Debugging a Failed Calendar Booking

**Scenario**: User says "I tried to book a meeting but it didn't work"

### Step 1: Get Session ID
```
User says call was at 3:15 PM
Search CloudWatch: timestamp = 2025-10-29 19:15:00
Find session ID in logs: CAW_xY2Z1a3b4c5d
```

### Step 2: Open Langfuse Trace
Go to Langfuse, search for `CAW_xY2Z1a3b4c5d`

### Step 3: Read the Trace
```
Timeline visible:
├── STT: "I'd like to schedule a meeting next Tuesday at 2pm"
│   └── Duration: 0.52s ✅
├── LLM: Recognized intent = schedule_meeting
│   └── Duration: 0.95s ✅
│   └── Extracted: date=2025-11-04, time=14:00
├── Tool: calendar.find_free_slots(date, duration)
│   └── ❌ FAILED after 3.2s
│   └── Error: "400 Bad Request - Invalid calendar scope"
├── TTS: Skipped (tool failed)
└── Session: Failed
    └── Message: "Sorry, I'm having trouble accessing the calendar"
```

### Step 4: Root Cause
**Google Calendar API scope issue** - service account doesn't have permission

### Step 5: Fix
1. Go to Google Cloud Console
2. Regenerate service account key
3. Add `calendar:read` scope
4. Update `.env.local` with new key
5. Redeploy agent
6. Ask user to retry call

---

## Quick Reference: Where to Find What

| Question | Where to Look | Time |
|----------|---------------|------|
| "Did the call fail?" | CloudWatch Dashboard or SNS alert | Instant |
| "What was the error?" | Recent Errors widget (session ID) | <1 min |
| "Exactly what went wrong?" | Langfuse trace for session | 1-2 min |
| "Which tool failed?" | Langfuse trace timeline | 1-2 min |
| "How long did it take?" | Langfuse shows each step duration | 1-2 min |
| "Was it slow or broken?" | Latency Breakdown widget | <1 min |
| "How many calls failed?" | Error Rate widget | <1 min |
| "Pattern of failures?" | Voice Agent - Error Rate query | 2-3 min |

---

## Common Failure Patterns & Fixes

### Pattern 1: Google Calendar API Failures (Most Common)
```
Trace shows: calendar.* operations failing
Error: "401 Unauthorized" or "403 Forbidden"

Fix:
1. Regenerate Google service account key
2. Verify GOOGLE_SERVICE_ACCOUNT_JSON path
3. Check calendar ID is accessible to service account
4. Redeploy agent
5. Test with probe call
```

### Pattern 2: LLM Rate Limiting
```
Trace shows: LLM timeout or 429 error
Error: "Rate limit exceeded"

Fix:
1. Check OpenAI usage/quota at platform.openai.com
2. Upgrade API tier if needed
3. Add exponential backoff to LLM calls
4. Monitor token usage in CloudWatch
```

### Pattern 3: Slow Responses (>2s)
```
Trace shows: One component taking >1.5s
Usually: Tool execution (calendar, CRM queries)

Fix:
1. Add query timeouts (max 1s per tool)
2. Cache results when possible
3. Optimize database queries
4. Use async operations
```

### Pattern 4: Silent Failures (No Error Message)
```
Trace shows: Session ended but no clear error
User reports: "Call just hung up"

Fix:
1. Check for unhandled exceptions in agent logs
2. Add try/catch around tool calls
3. Set session timeout (max 5 minutes)
4. Log all state transitions
```

### Pattern 5: Audio/STT Issues
```
Trace shows: STT returning empty or garbled text
Error: "No speech detected" or random characters

Fix:
1. Check caller's microphone/audio
2. Verify AssemblyAI API key is valid
3. Test STT with clean audio sample
4. Add audio level validation before STT
```

---

## Monitoring Script (Check These Daily)

```bash
# Run these queries to stay on top of issues

# 1. Yesterday's error rate
aws logs start-query \
  --log-group-name "CA_9b4oemVRtDEm" \
  --start-time $(date -u -d '24 hours ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string "fields @message | filter @message like /ERROR/ | stats count() as errors" \
  --region us-west-1

# 2. Slowest calls yesterday
aws logs start-query \
  --log-group-name "CA_9b4oemVRtDEm" \
  --start-time $(date -u -d '24 hours ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string "fields total_latency | filter _event_type = \"voice_metrics\" | stats percentile(total_latency, 95) as p95" \
  --region us-west-1

# 3. Most common failures
aws logs start-query \
  --log-group-name "CA_9b4oemVRtDEm" \
  --start-time $(date -u -d '24 hours ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string "fields @message | filter @message like /ERROR/ | stats count() as count by @message | sort count desc | limit 10" \
  --region us-west-1
```

---

## Alert Response Checklist

When you get a **VoiceAgent-HighErrorRate alert**:

- [ ] Open CloudWatch dashboard
- [ ] Check "Recent Errors" widget for session IDs
- [ ] Pick one session ID and open Langfuse
- [ ] Read the trace to find failure point
- [ ] Identify which component failed (STT, LLM, Tool, TTS)
- [ ] Check troubleshooting section above for that component
- [ ] Fix the issue (credentials, API key, timeout, etc.)
- [ ] Test with probe call (have someone call to verify fix)
- [ ] Verify error rate returns to normal on dashboard

**Total time**: 5-10 minutes from alert to fix

---

## Pro Tips for Debugging

1. **Always start with Langfuse traces first** - They show the complete picture
2. **Look for the first RED item** - That's usually the root cause
3. **Check timestamps** - Often reveals rate limiting or timeout issues
4. **Test fixes with probe calls** - Don't assume it's fixed without testing
5. **Watch the dashboard** - See if error rate improves after fix
6. **Save session IDs** - Keep them for pattern analysis
7. **Monitor token usage** - Can predict LLM failures before they happen

---

## Example: Complete Debugging Session (Real-World)

**Timestamp**: 2025-10-29 15:00 UTC
**Alert**: `VoiceAgent-HighErrorRate` alarm triggered
**Your action**: 2 minutes to resolution

```
15:02 - Get SNS alert: HighErrorRate alarm triggered
15:03 - Open dashboard, see 12 errors in "Recent Errors" widget
15:04 - Click on top error session ID: CAW_abc123xyz
15:05 - Open Langfuse, search for session
15:06 - Read trace timeline:
       STT ✅ → LLM ✅ → Calendar Tool ❌ (401 Unauthorized)
15:07 - Root cause: Google Calendar API key expired
15:08 - Regenerate key in Google Cloud Console
15:09 - Update .env.local with new key
15:10 - Deploy agent: `lk agent deploy`
15:12 - Ask team member to make test call
15:13 - Test call succeeds, trace shows all green ✅
15:14 - Monitor dashboard: error rate dropping
15:15 - Close alert, crisis over ✅
```

**Time to resolution: 13 minutes**
**Root cause identified: 5 minutes**
**Root cause fixed: 3 minutes**

---

## Summary

When a call fails, you'll know through:
1. **SNS alerts** (real-time, automated)
2. **Dashboard widgets** (manual checks, always available)
3. **User reports** (reactive, but complete context)

To debug, follow this process:
1. Get the session ID (from alert, dashboard, or logs)
2. Open Langfuse and load the trace
3. Read the timeline and find the first ❌
4. Check the troubleshooting section for that failure type
5. Apply the fix
6. Test with a probe call
7. Verify dashboard shows improvement

**Most failures are fixed in 5-10 minutes once you have the trace.**

The key insight: **Langfuse traces are your superpower** - they show exactly what happened, not just that something went wrong.

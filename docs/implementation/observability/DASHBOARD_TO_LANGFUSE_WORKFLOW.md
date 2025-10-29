# Dashboard to Langfuse Workflow - One-Click Debugging

**Time to Debug**: 30 seconds
**Tools**: CloudWatch Dashboard + Langfuse
**Goal**: From dashboard alert → Full trace in Langfuse with one click

---

## Quick Start: Dashboard → Langfuse

### **Step 1: Open Your Dashboard**
[https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance)

### **Step 2: Find the Error**
Look for one of these three widgets:
- **"Recent Errors (Last 10)"** - Click to see recent failures
- **"Slow Sessions (>2s latency)"** - Click to debug slow calls
- **"Qualified Leads (24h)"** - Click to see lead session details

Each widget now shows **clean, readable columns**:
- `timestamp` - When it happened
- `session_id` - The session to debug ← **Copy this**
- Error/latency details specific to that widget

### **Step 3: Copy the Session ID**
1. Look at the widget results
2. Find the row with the issue
3. **Select and copy the `session_id` value**
   - Example: `CAW_abc123xyz`

### **Step 4: Open Langfuse**
Go to [https://us.cloud.langfuse.com](https://us.cloud.langfuse.com)

### **Step 5: Search for Session**
1. In the top search bar, paste the session ID
2. Press Enter
3. See the full trace with complete timeline

### **Step 6: Read the Trace**
Trace shows you exactly what happened:
```
Timeline (read top to bottom):
✅ STT: Transcribed audio successfully
✅ LLM: Generated response
❌ Tool: Calendar API failed - 401 Unauthorized
❌ TTS: Skipped (due to tool failure)
```

The first ❌ is your root cause.

---

## Dashboard Widgets Explained

### Widget 1: "Recent Errors (Last 10) - Click Session ID to View in Langfuse"

**What it shows:**
```
timestamp              session_id         error_message
2025-10-29 20:15:00   CAW_abc123xyz     ERROR: Calendar API rate limited
2025-10-29 20:14:45   CAW_def456uvw     ERROR: Google Auth token expired
2025-10-29 20:14:30   CAW_ghi789rst     ERROR: Network timeout on LLM call
```

**When to use:**
- User reports a call failed
- Error rate alarm triggered
- You want to see what's breaking

**To debug:**
1. Find the row with the time of the failure
2. Copy the `session_id`
3. Paste into Langfuse search
4. Read trace to find exact failure point

---

### Widget 2: "Slow Sessions (>2s latency) - Click Session ID to Analyze"

**What it shows:**
```
timestamp              session_id         latency_seconds  eou_delay  llm_ttft  tts_ttfb
2025-10-29 20:10:00   CAW_jkl012mno     3.2s             0.45s      0.87s     1.2s
2025-10-29 20:09:45   CAW_pqr345stu     2.8s             0.40s      1.8s      0.3s
2025-10-29 20:09:30   CAW_vwx678yz      2.5s             0.52s      1.2s      0.6s
```

**When to use:**
- User says "The agent is slow"
- You want to optimize performance
- Need to identify which component is bottleneck

**To debug:**
1. Find the row with high latency
2. Copy the `session_id`
3. Paste into Langfuse
4. Trace shows exactly which component took longest
5. Example: If `llm_ttft` is high, the LLM is slow → Check OpenAI quota

---

### Widget 3: "Qualified Leads (24h) - Click Session ID to Debug"

**What it shows:**
```
timestamp              session_id         team_size  volume
2025-10-29 20:10:00   CAW_aaa111bbb     12         250
2025-10-29 20:05:00   CAW_ccc222ddd     8          500
2025-10-29 19:55:00   CAW_eee333fff     15         1200
```

**When to use:**
- Following up on qualified leads
- Need conversation details for a lead
- Want to verify what the agent discussed

**To debug:**
1. Find the lead row
2. Copy the `session_id`
3. Paste into Langfuse
4. Trace shows the entire conversation
5. Review what the lead said and what the agent recommended

---

## Why Clean Queries Matter

**Before (messy):**
```
@log          @logGroupId    @logStream    @logStreamId    @timestamp         _session_id      message
...bunch...   ee19           CAM_...      ee19            1761              CAW_abc123xyz    ERROR...
              of junk                                       [timestamp]
```
❌ Hard to read, can't see session ID easily

**After (clean):**
```
timestamp              session_id         error_message
2025-10-29 20:15:00   CAW_abc123xyz     ERROR: Calendar API rate limited
```
✅ Crystal clear, session ID easy to copy

---

## The Full Workflow: From Alert to Fix

```
1. Get SNS Alert
   ↓
2. Open CloudWatch Dashboard
   ↓
3. Check "Recent Errors" or "Slow Sessions" widget
   ↓
4. Find the problem row
   ↓
5. Copy session_id (now visible and clean!)
   ↓
6. Go to Langfuse, paste session_id
   ↓
7. Read trace, find ❌ failure
   ↓
8. Identify root cause
   ↓
9. Fix (regen credentials, increase timeout, etc.)
   ↓
10. Test with probe call
   ↓
11. Verify dashboard shows improvement ✅

Total time: 2-5 minutes
```

---

## Langfuse URL Reference

**Direct link to Langfuse:**
https://us.cloud.langfuse.com

**Search for a session:**
1. Click "Traces" in left sidebar
2. Use the filter/search box at the top
3. Paste your session ID
4. Click the result to open full trace

**View timeline:**
- Trace shows vertical timeline of all events
- Each box is a "span" (operation like STT, LLM, etc.)
- Green = success, Red = failure
- Click any span to see details

---

## Common Scenarios

### Scenario 1: User Says "Call Failed"
```
Action:
1. Get approximate call time from user
2. Open dashboard, check "Recent Errors" widget
3. Find error around that time
4. Copy session_id
5. Open Langfuse, paste session_id
6. Read trace to find what failed
7. See troubleshooting guide in DEBUGGING_FAILED_CALLS.md
```

### Scenario 2: Error Rate Alarm Triggers
```
Action:
1. Check SNS email
2. Open dashboard immediately
3. Look at "Recent Errors" widget
4. Pick any session_id
5. Open Langfuse
6. Read trace to find pattern (same failure repeated?)
7. If yes, fix root cause
8. If no, investigate each one
```

### Scenario 3: Performance Degradation
```
Action:
1. Notice P95 latency increasing
2. Open dashboard
3. Check "Slow Sessions" widget
4. Pick a slow session_id
5. Open Langfuse
6. Check which component is slow (eou_delay, llm_ttft, tts_ttfb)
7. Optimize that component
```

### Scenario 4: Following Up on Leads
```
Action:
1. Morning: Check "Qualified Leads" widget
2. Pick a high-value lead session_id
3. Open Langfuse
4. Review full conversation
5. See what the lead asked for, what agent recommended
6. Use this info for follow-up call/email
```

---

## Pro Tips

**1. Bookmark Langfuse**
Save this link: https://us.cloud.langfuse.com
Makes it instant to jump from dashboard to traces

**2. Use the Dashboard Time Selector**
Top of dashboard has time options: `1h`, `3h`, `12h`, `1d`, `Custom`
Use these to focus on the relevant timeframe

**3. Session IDs Follow a Pattern**
- Always start with `CA` or `CAW`
- Example: `CAW_3Y7MVDtgE8xm`
- Copy exactly, paste into Langfuse

**4. Read Traces Top to Bottom**
The timeline is chronological - first ❌ is usually the root cause

**5. Watch for Rate Limiting**
If you see lots of 429 errors in traces, you're hitting API limits
Check: OpenAI quota, Google API quota, Deepgram usage

---

## Troubleshooting the Workflow

**"I copied the session ID but Langfuse shows no results"**
- Check spelling (copy/paste, don't type)
- Try without the `CA` prefix
- Session might be older than Langfuse retention (default 7 days)
- Check you're in the right Langfuse project

**"Dashboard widget shows no data"**
- Click the time selector at top, try `3h` instead of `1h`
- Check that agent has been running and receiving calls
- Verify log group has data: `aws logs tail CA_9b4oemVRtDEm --since 1h`

**"Session ID not visible in widget"**
- The widget should now show `session_id` column (we fixed this)
- If still not showing, refresh the page
- Try expanding rows if truncated

---

## Summary

The updated dashboard makes debugging elegant and fast:

✅ **Clean columns** - Only show what matters (timestamp, session_id, error/latency)
✅ **Easy to scan** - Visual hierarchy shows the most important info first
✅ **Session IDs visible** - Copy directly from dashboard
✅ **Langfuse integration** - Paste session ID, get full trace
✅ **Widget titles hint at usage** - "Click Session ID to View in Langfuse"

**Time from "call failed" to "I know what broke": 2-5 minutes**

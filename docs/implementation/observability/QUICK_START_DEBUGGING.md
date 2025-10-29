# Quick Start: 30-Second Debugging

**Scenario**: A call failed. You need to know why.

---

## The 30-Second Path to Root Cause

### **Step 1: Open Dashboard** (5 seconds)
[https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance)

### **Step 2: Find Error** (5 seconds)
Look at **"Recent Errors (Last 10)"** widget (bottom right)
- See timestamp of when error happened?
- Find it in the table

### **Step 3: Copy Session ID** (5 seconds)
Click on that row, copy the `session_id` column
- Example: `CAW_abc123xyz`

### **Step 4: Open Langfuse** (5 seconds)
[https://us.cloud.langfuse.com](https://us.cloud.langfuse.com)

### **Step 5: Paste & Search** (5 seconds)
1. Click search box
2. Paste session ID
3. Press Enter
4. Click the trace to open

### **Step 6: Find the RED** (5 seconds)
Read the timeline top to bottom.
Find the first ❌ (red item).
That's your problem.

---

## Example: You Get an Alert at 3:15 PM

```
Alert: VoiceAgent-HighErrorRate triggered

Your action:
1. Click dashboard link (5s)
2. Find error at 3:15 PM in "Recent Errors" (5s)
3. Copy: CAW_xyz789abc (5s)
4. Go to Langfuse (5s)
5. Paste and search (5s)
6. Read timeline:
   ✅ STT: OK
   ✅ LLM: OK
   ❌ TOOL: Calendar API 401 Unauthorized ← HERE'S YOUR PROBLEM
7. Fix: Regenerate Google service account key

Total time: 30-45 seconds to identify root cause
```

---

## What Each Widget Shows You

| Widget | Shows | Use For |
|--------|-------|---------|
| **Recent Errors** | Failed calls | User said "call failed" |
| **Slow Sessions** | Calls >2s | User said "it was slow" |
| **Qualified Leads** | High-value callers | Follow-up or conversion tracking |

All widgets now show: `timestamp`, `session_id`, and details
Session ID is easy to copy → paste into Langfuse

---

## Common Failures (What to Look For in Trace)

### ❌ Calendar API Failed
```
Error: 401 Unauthorized or 403 Forbidden
Fix: Regenerate Google service account key
```

### ❌ LLM Timed Out
```
Error: Timeout after 15+ seconds or 429 rate limit
Fix: Check OpenAI quota, wait for reset, or upgrade plan
```

### ❌ Audio Issue
```
Error: "No speech detected" or garbled transcription
Fix: Ask caller to speak clearly, check microphone
```

### ❌ TTS Failed
```
Error: Cartesia timeout or 500 error
Fix: Check TTS service status, simplify response
```

### ⚠️ Just Slow (Not Failed)
```
Trace shows all ✅ but latency >2s
Bottleneck: Check which component took longest
- If LLM TTFT high: OpenAI is slow
- If Tool long: Database/API query is slow
- If TTS TTFB high: Voice service is slow
```

---

## Dashboard + Langfuse = Fast Debugging

```
CloudWatch Dashboard        Langfuse
     ↓                        ↓
Find session_id ────→ Paste into search
     ↓                        ↓
See timestamp        Get full trace timeline
     ↓                        ↓
Identify issue ◄──── See exact failure point
     ↓
Apply fix
```

---

## Bookmark These

**Dashboard**: https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance

**Langfuse**: https://us.cloud.langfuse.com

**Full Debugging Guide**: See `DEBUGGING_FAILED_CALLS.md` in this directory

---

## You're Now Ready

You have:
✅ CloudWatch Dashboard showing real-time errors
✅ Clean queries showing session IDs
✅ Langfuse for full trace analysis
✅ This guide for 30-second debugging

**When something goes wrong, you'll know exactly what happened in < 1 minute.**

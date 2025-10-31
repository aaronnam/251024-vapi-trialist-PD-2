# Transcript Capture Fix - Deployed with Diagnostic Logging

**Date**: October 31, 2025
**Status**: ✅ Deployed to Production
**Agent Version**: v20251031044526

---

## What Was Changed

### Code Changes (agent.py:1528-1589)

Added comprehensive diagnostic logging to the transcript extraction code to understand why transcripts are empty:

1. **Explicit ChatMessage Type Filtering**
   - Import `livekit.agents.llm` module properly
   - Filter `session.history` for `ChatMessage` instances only
   - Log total items vs. ChatMessage items

2. **Detailed Logging at Each Step**
   - Log number of items in session.history
   - Log types of first 5 items for debugging
   - Log each ChatMessage processing with role
   - Log successful captures with message preview
   - Log warnings for messages with no text content

3. **Improved Error Handling**
   - Catch and log exceptions during message processing
   - Continue processing remaining messages if one fails
   - Full traceback on critical failures

### Example Log Output (Expected)

**If session.history has messages:**
```
🔍 Transcript extraction: 4 items in session.history
🔍 Found 4 ChatMessage items (filtered from 4 total)
🔍 Item 0: type=ChatMessage, role=user
🔍 Item 1: type=ChatMessage, role=assistant
🔍 Processing ChatMessage 0: role=user
✅ Captured user message: Yes, I'm comfortable with that...
🔍 Processing ChatMessage 1: role=assistant
✅ Captured assistant message: Great! I'm here to help you get the most...
✅ Transcript extraction complete: 4 messages captured
```

**If session.history is empty:**
```
🔍 Transcript extraction: 0 items in session.history
🔍 Found 0 ChatMessage items (filtered from 0 total)
✅ Transcript extraction complete: 0 messages captured
```

**If session.history doesn't exist:**
```
⚠️ session.history is None or doesn't exist
```

---

## How to Test

### 1. Make a Test Call

Call the agent and:
1. Give consent when asked: "Yes, I'm comfortable with that"
2. Ask a question after consent: "How do I integrate with Salesforce?"
3. Wait for the agent's response
4. End the call normally

### 2. Check Logs for Diagnostic Output

```bash
# View live logs with diagnostic emoji markers
lk agent logs | grep "🔍\|✅\|⚠️"

# Or search for specific transcript extraction logs
lk agent logs | grep "Transcript extraction"

# Get the full log context around transcript extraction
lk agent logs | grep -A 20 "Transcript extraction:"
```

### 3. What to Look For

#### Good Signs ✅
- `🔍 Transcript extraction: X items in session.history` (X > 0)
- `🔍 Found Y ChatMessage items` (Y > 0)
- `✅ Captured user message: ...`
- `✅ Captured assistant message: ...`
- `✅ Transcript extraction complete: N messages captured` (N > 0)

#### Bad Signs ❌
- `🔍 Transcript extraction: 0 items in session.history`
- `⚠️ session.history is None or doesn't exist`
- `⚠️ ChatMessage 0 (role=user) has no text content`
- `❌ Transcript extraction failed: ...`

#### Interesting Signs 🤔
- `🔍 Item 0: type=FunctionCall, role=N/A` (means history has tool calls mixed in)
- `🔍 Found 2 ChatMessage items (filtered from 8 total)` (means filtering is working)

### 4. Verify S3 Upload

After making a test call, check if the transcript was saved to S3:

```bash
# List recent session files
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
  --region us-west-1 \
  | tail -5

# Download and check the latest file
aws s3 cp s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/$(
  aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
    --region us-west-1 \
    | tail -1 \
    | awk '{print $4}'
) /tmp/latest_session.json.gz --region us-west-1

# Extract and view transcript
gunzip -c /tmp/latest_session.json.gz | jq '.transcript, .transcript_text'
```

---

## Next Steps Based on Log Results

### Scenario A: History Has Items but No ChatMessages

**Logs show:**
```
🔍 Transcript extraction: 8 items in session.history
🔍 Found 0 ChatMessage items (filtered from 8 total)
🔍 Item 0: type=FunctionCall, role=N/A
🔍 Item 1: type=FunctionCallOutput, role=N/A
```

**This means:** session.history contains tool calls/outputs but not conversation messages.

**Fix:** Use event-based capture instead of shutdown-based extraction. See `TRANSCRIPT_CAPTURE_DIAGNOSIS.md` Fix #3 (conversation_item_added event).

### Scenario B: History Is Always Empty

**Logs show:**
```
🔍 Transcript extraction: 0 items in session.history
✅ Transcript extraction complete: 0 messages captured
```

**This means:** session.history is not being populated during the conversation.

**Possible causes:**
1. Conversation ending before messages are committed
2. session.history not being updated in GREETING state
3. Timing issue where shutdown happens before history is populated

**Fix:** Use event-based capture (Fix #3 in diagnosis doc) to capture messages as they happen instead of at shutdown.

### Scenario C: History Has Messages but No Text Content

**Logs show:**
```
🔍 Processing ChatMessage 0: role=user
⚠️ ChatMessage 0 (role=user) has no text content
🔍 Processing ChatMessage 1: role=assistant
✅ Captured assistant message: ...
```

**This means:** User messages are in history but their content is not being extracted correctly.

**Fix:** Check if user messages have a different content structure. May need to handle audio content or check for different content item types.

### Scenario D: Everything Works! 🎉

**Logs show:**
```
🔍 Transcript extraction: 4 items in session.history
🔍 Found 4 ChatMessage items (filtered from 4 total)
✅ Captured user message: Yes, I'm comfortable with that
✅ Captured assistant message: Great! I'm here to help...
✅ Transcript extraction complete: 4 messages captured
```

**This means:** The code is working correctly! Transcripts should now appear in S3.

**Verify:**
- Check S3 for the session file
- Verify `transcript` array is populated
- Verify `transcript_text` field has content
- Check Langfuse for the same session to confirm consistency

---

## Troubleshooting

### Logs Don't Show Any Diagnostic Output

**Problem:** No 🔍 emojis in logs after a test call.

**Possible causes:**
1. Agent didn't restart properly - try `lk agent restart` again
2. Call ended before export_session_data() ran
3. Viewing old logs - make sure you're looking at recent logs

**Check:**
```bash
# Verify agent status and version
lk agent status

# Should show: Image version: v20251031044526 or newer

# Stream fresh logs
lk agent logs --follow
```

### Still Getting Empty Transcripts After Fix

**Problem:** Logs show successful capture but S3 still has empty transcripts.

**Possible causes:**
1. Looking at old session files (before the fix)
2. S3 upload is failing (check for S3 errors in logs)
3. Different code path is being used

**Check:**
```bash
# Search for S3 upload success messages
lk agent logs | grep "Analytics uploaded to S3"

# Search for S3 upload failures
lk agent logs | grep "S3 upload failed"

# Verify the session timestamp matches your test call
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/ \
  --region us-west-1 \
  | tail -5
```

---

## Deployment Details

**Git Commit:** 706d764
**Deployment Command:** `lk agent deploy`
**Restart Command:** `lk agent restart`
**Docker Cache Busted:** Yes (via .dockerignore timestamp)

**Files Changed:**
- `my-app/src/agent.py` (lines 1528-1589)
- `my-app/.dockerignore` (cache bust comment)

---

## Summary

✅ **Deployed:** Diagnostic logging is now active in production
📊 **Purpose:** Understand why transcripts are empty
🔍 **Next Action:** Make a test call and review logs
📝 **Expected Outcome:** Logs will reveal the root cause

Once we see the diagnostic logs from a real call, we'll know exactly what's wrong and can apply the appropriate fix from `TRANSCRIPT_CAPTURE_DIAGNOSIS.md`.

# Verify User ID is Working - Quick Checklist

**Status**: Implementation deployed
**What to Check**: 3 places to verify user ID is flowing to Langfuse
**Time to Verify**: ~2 minutes

---

## Step 1: Check Agent Logs (30 seconds)

Run this command:
```bash
lk agent logs --tail 30 | grep -E "Langfuse|user_id|participant_identified"
```

**Look For**:
```
✅ Langfuse updated with user ID: customer@example.com
✅ Tracing enabled for session CAW_abc123xyz
✅ Session started for email: customer@example.com
```

**If You See**: The success message ✅ confirms User ID is being captured

**If You See**: "Could not update Langfuse with user ID" - Check that Langfuse keys are set in LiveKit Cloud secrets

---

## Step 2: Run a Test Call (1 minute)

### Option A: Terminal Console (Easiest for Testing)
```bash
cd my-app
uv run python src/agent.py console
```

Then speak to the agent. When you hang up, check logs for the user ID message.

### Option B: Via Frontend/Web
If you have a frontend set up, send a test message with metadata containing `user_email`

---

## Step 3: Check Langfuse Filters (1 minute)

### Go to Langfuse Dashboard
1. Open: https://us.cloud.langfuse.com
2. Navigate to your traces
3. Click the **Filters** button on the left
4. Look for the **User ID** dropdown

### Expected Results

**BEFORE** (what you saw earlier):
```
User ID: [Dropdown showing "No options found"]
```

**AFTER** (what you should see now):
```
User ID: [Dropdown showing available email addresses like:]
         - customer@company.com
         - john@example.com
         - jane@example.com
```

If you see actual emails in the dropdown → **User ID implementation is working!** ✅

---

## Complete Verification Workflow

### 1. Check Logs
```bash
lk agent logs | grep -i "langfuse updated"
```
✅ See success message = good sign

### 2. View Recent Traces
Go to https://us.cloud.langfuse.com
- Look at **recent traces**
- Click on one trace
- Should show **User: customer@email.com** in trace details

### 3. Test Filter
In Langfuse:
1. Click **Filters**
2. Select **User ID** dropdown
3. See emails listed = Working! ✅

### 4. Filter by User
1. Select a user from dropdown
2. All traces for that user appear
3. You can now see user's full call history ✅

---

## Troubleshooting

### Issue: "No options found" still appears in Langfuse

**Check**:
1. Have you run a test call YET?
   - New traces are needed to populate filters
   - Run: `uv run python src/agent.py console`

2. Is the call passing `user_email` in metadata?
   - Check your frontend/test is sending metadata
   - Metadata must be valid JSON: `{"user_email": "test@example.com"}`

3. Are Langfuse secrets correct in LiveKit Cloud?
   ```bash
   lk agent secrets | grep LANGFUSE
   ```
   - Both `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` must be set
   - If missing: `lk agent update-secrets --secrets-file .env.local && lk agent restart`

4. Has the agent been restarted after code deployment?
   - Deployment auto-restarts, but verify:
   ```bash
   lk agent status
   ```
   - Should show recent restart time matching deployment

### Issue: Logs show "Could not update Langfuse with user ID"

**Check**:
1. Is `trace_provider` None?
   - Means Langfuse keys missing
   - Check: `lk agent secrets | grep LANGFUSE`

2. Is OpenTelemetry available?
   - Should be included in dependencies
   - Check: `uv pip list | grep opentelemetry`

3. Check full error in logs:
   ```bash
   lk agent logs | grep "Could not update"
   ```
   - Shows actual exception message

---

## Success Indicators

| Indicator | Status |
|-----------|--------|
| Agent logs show "Langfuse updated with user ID" | ✅ User ID captured |
| Langfuse shows emails in User ID filter | ✅ User ID transmitted |
| Can filter traces by user email | ✅ User ID filtering works |
| Trace details show "User: email@company.com" | ✅ User ID visible in traces |
| Can see call history for single user | ✅ Full implementation working |

---

## What's Different Now

### In Agent Logs
**NEW**: `✅ Langfuse updated with user ID: customer@company.com`

### In Langfuse UI Filters
**BEFORE**: User ID dropdown = "No options found"
**AFTER**: User ID dropdown = [customer@company.com, jane@example.com, ...]

### In Trace Details
**BEFORE**: Session: CAW_abc123xyz (only)
**AFTER**: Session: CAW_abc123xyz, User: customer@company.com ✅

---

## Quick Reference Links

| Resource | URL |
|----------|-----|
| **Agent Logs** | `lk agent logs \| grep langfuse` |
| **Langfuse Dashboard** | https://us.cloud.langfuse.com |
| **Trace Filters** | Click "Filters" → "User ID" dropdown |
| **Full Documentation** | See `LANGFUSE_USER_ID_GUIDE.md` |
| **Implementation Details** | See `USER_ID_IMPLEMENTATION_SUMMARY.md` |

---

## Testing Checklist

- [ ] Run `lk agent logs` and see "Langfuse updated" message
- [ ] Do test call via console or frontend
- [ ] Go to Langfuse filters
- [ ] See User ID dropdown shows email addresses
- [ ] Click User ID and filter by specific email
- [ ] Verify traces appear for that user
- [ ] Check trace details show user email

**Total time**: ~2-3 minutes to fully verify

---

**Status**: Implementation deployed and ready to test
**Next**: Follow steps above to verify it's working

# S3 Data Export Summary

**4. The data that we will extract and put into an S3 bucket are:**

**Session Metadata**:
- Session ID, start/end times, duration
- User identification (email, name, participant ID)

**Complete Conversation Data**:
- Full transcript with user/agent messages
- Turn-taking metrics (interruption counts, turn balance)
- Timestamps for all interactions

**Discovered Qualification Signals** (extracted from natural conversation):
- Team size, monthly document volume
- Integration needs (Salesforce, HubSpot, etc.)
- Industry, location, use case
- Current tools, pain points
- Decision timeline, budget authority
- Urgency level and qualification tier (Tier 1/2)

**Voice Performance Metrics** (LiveKit built-in):
- Latency metrics (end-of-utterance delay, LLM response time, TTS latency)
- Token usage (prompt/completion/total tokens)
- Audio durations (STT/TTS processing times)

**Tool Usage Tracking**:
- Knowledge base searches (queries, categories, results found)
- Meeting bookings (customer info, success/failure)
- Timestamps for all tool calls

All data is stored as compressed JSON (GZIP) in S3 with date partitioning (year/month/day), enabling SQL queries via Athena and integration with Salesforce/Amplitude for downstream analytics.

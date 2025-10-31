# How to Find & Debug Your CEO's CPQ Conversation in Langfuse

## Quick Action Plan (2 minutes to find the conversation)

### Step 1: Identify When the Call Happened
Ask your CEO or check:
- Approximate time of the call (e.g., "around 2:30 PM today")
- Any unique identifiers (session ID if available)
- Phone number or email they used (if tracked)

### Step 2: Find the Session in Langfuse

#### Option A: Search by Time Range (Most Common)
1. Open Langfuse: https://us.cloud.langfuse.com
2. Go to **Traces** view
3. Use the **time filter** (top right):
   - Set start time to 15 minutes before the call
   - Set end time to 15 minutes after
4. Look for traces with "CPQ" in the content

#### Option B: Full-Text Search for CPQ Content
1. In Langfuse Traces view
2. Use the **search bar** at the top
3. Search for: `"CPQ"` or `"configure price quote"`
4. Filter by today's date
5. Look for traces matching the CEO's conversation timing

#### Option C: Search via CloudWatch Dashboard First
```bash
# If you know approximate time, use CloudWatch to get session ID
aws logs filter-log-events \
  --log-group-name "CA_9b4oemVRtDEm" \
  --start-time $(date -u -d '2 hours ago' +%s)000 \
  --filter-pattern '"CPQ"' \
  --region us-west-1 \
  --query 'events[*].message' \
  --output text | grep -i session
```

### Step 3: Analyze the Conversation

Once you find the trace:

1. **Click on the trace** to expand the full conversation timeline
2. **Look for these key elements:**
   ```
   Timeline Structure:
   ├── STT (Speech-to-Text)
   │   └── Look for: CEO's actual question about CPQ
   ├── LLM Processing
   │   └── Look for: How the model interpreted the question
   │   └── Check: Did it recognize "CPQ" intent?
   ├── Tool Calls (if any)
   │   └── Check: Did it try to search knowledge base?
   ├── TTS (Text-to-Speech)
   │   └── The actual response given to CEO
   ```

3. **Identify the failure point:**
   - ❌ **LLM didn't understand CPQ** → System prompt needs CPQ context
   - ❌ **No tool call for knowledge search** → Add CPQ to search triggers
   - ❌ **Wrong information returned** → Update knowledge base
   - ❌ **Correct info but unclear** → Improve response formatting

## Finding Specific Conversation Turns

### To Find Individual Turns Within the Conversation:

1. **In the trace view**, look for "observations" (sub-spans)
2. Each observation represents a turn:
   - `generation` type = LLM response
   - `span` type with tool name = Tool execution
   - Look for observation names like `stt`, `llm`, `tts`

3. **Click on specific observations** to see:
   - Input (what was said/asked)
   - Output (what was responded)
   - Metadata (timing, tokens, etc.)

### Example: Finding the CPQ Question Turn

```python
# If you need to search programmatically
from langfuse import Langfuse

langfuse = Langfuse()

# Search for traces containing CPQ mentions
traces = langfuse.api.trace.list(
    limit=100
)

# Filter for CPQ content
cpq_traces = [
    t for t in traces
    if t.input and "CPQ" in str(t.input).upper()
    or t.output and "CPQ" in str(t.output).upper()
]

# Get the specific conversation
for trace in cpq_traces:
    print(f"Session: {trace.session_id}")
    print(f"Time: {trace.timestamp}")
    print(f"User said: {trace.input}")
    print(f"Agent responded: {trace.output}")
```

## How to Fix the CPQ Issue

### Step 1: Identify What Went Wrong

Based on the trace, determine:

| Issue | Solution |
|-------|----------|
| Agent doesn't know what CPQ means | Add CPQ definition to system prompt |
| Agent knows CPQ but gave wrong info | Update knowledge base with correct CPQ content |
| Agent couldn't find CPQ info | Add CPQ search terms to tool descriptions |
| Response was too vague | Add specific CPQ examples to prompt |

### Step 2: Update the System Prompt

Edit `/my-app/src/agent.py` and update the instructions:

```python
# Current location around line 135-200
SYSTEM_PROMPT = """You are Olivia, an AI assistant for PandaDoc...

# ADD THIS SECTION:
## Product Knowledge

### CPQ (Configure, Price, Quote)
CPQ is PandaDoc's advanced quoting solution that enables:
- Dynamic pricing based on product configurations
- Automated quote generation with custom pricing rules
- Product bundling and discount management
- Integration with CRM systems for seamless quote-to-cash workflows

When users ask about CPQ, explain:
1. It helps sales teams create accurate, professional quotes quickly
2. Reduces pricing errors through automated calculations
3. Speeds up the sales cycle with instant quote generation
4. Key features: product catalog, pricing rules, approval workflows, and quote templates

If users need detailed CPQ setup help, offer to:
- Search the knowledge base for specific CPQ guides
- Schedule a meeting with a CPQ specialist
- Send CPQ documentation via email
"""
```

### Step 3: Add CPQ as a Search Trigger

Update the search tool to recognize CPQ queries:

```python
# In your search_knowledge_base function
def search_knowledge_base(query: str) -> str:
    # Add CPQ-specific search enhancement
    if any(term in query.upper() for term in ['CPQ', 'CONFIGURE PRICE QUOTE', 'QUOTING']):
        # Enhance query with CPQ-specific terms
        enhanced_query = f"{query} CPQ configure price quote pricing rules product catalog"
        return unleash_search(enhanced_query)
    else:
        return unleash_search(query)
```

### Step 4: Test the Fix

1. **Deploy the updated agent:**
   ```bash
   lk agent deploy
   lk agent restart
   ```

2. **Test in console mode first:**
   ```bash
   uv run python src/agent.py console
   # Ask: "What is CPQ and how does it work?"
   # Ask: "How do I set up CPQ in PandaDoc?"
   ```

3. **Create a test trace to verify:**
   - Make a test call
   - Ask the CPQ question
   - Find in Langfuse using same search method
   - Verify the response is now correct

## Monitoring CPQ Conversations Going Forward

### Set Up CPQ-Specific Tracking

1. **Add CPQ tag when detected:**
```python
# In your agent conversation handler
if "CPQ" in user_message.upper():
    # Add tag to trace for easy filtering
    langfuse_context.update_current_trace(
        tags=["cpq-inquiry"],
        metadata={"topic": "CPQ", "question_type": "product_info"}
    )
```

2. **Create a saved filter in Langfuse:**
   - Go to Traces view
   - Set filter: Tags contains "cpq-inquiry"
   - Save this view as "CPQ Conversations"

3. **Set up CloudWatch alert for CPQ issues:**
```bash
# Create alert for failed CPQ responses
aws logs put-metric-filter \
  --log-group-name "CA_9b4oemVRtDEm" \
  --filter-name "CPQErrors" \
  --filter-pattern '[time, request_id, level = "ERROR", ... , message = "*CPQ*"]' \
  --metric-transformations \
    metricName=CPQErrors,\
    metricNamespace=VoiceAgent,\
    metricValue=1
```

## Quick Reference: Search Patterns

| What You're Looking For | Search Method |
|------------------------|---------------|
| CEO's specific call | Time range + "CPQ" text search |
| All CPQ conversations | Tag filter: "cpq-inquiry" |
| Failed CPQ responses | Error level + "CPQ" in message |
| CPQ by specific user | User ID + "CPQ" text search |
| Today's CPQ questions | Date filter + "CPQ" search |

## Troubleshooting Tips

1. **Can't find the conversation?**
   - Expand time range (CEO might have wrong time)
   - Search for related terms: "pricing", "quote", "configure"
   - Check if tracing was enabled at that time

2. **Found trace but no CPQ mention?**
   - CEO might have used different terms
   - Check the STT transcription accuracy
   - Look for traces immediately before/after

3. **Multiple similar conversations?**
   - Use metadata to identify (phone number, user ID)
   - Check conversation duration
   - Look for specific phrases CEO mentioned

## Summary Checklist

When debugging CPQ or similar issues:

- [ ] Find the conversation using time range + text search
- [ ] Identify the exact question in STT observation
- [ ] Check how LLM interpreted it
- [ ] See if appropriate tools were called
- [ ] Review the actual response given
- [ ] Update system prompt with missing context
- [ ] Add search triggers for the topic
- [ ] Test fix in console mode
- [ ] Deploy and verify with test call
- [ ] Set up monitoring for future occurrences

**Time to resolution: 5-10 minutes from identification to fix deployment**
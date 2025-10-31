# Langfuse Search & Filtering Guide

Comprehensive guide for effectively searching, filtering, and organizing traces in Langfuse for debugging conversations, monitoring agent behavior, and analyzing performance issues.

## Quick Start: Search Patterns

### 1. Filter by Session ID (Group Related Traces)

**Via UI:**
- Open the Traces view in Langfuse dashboard
- Look for "Session" filter dropdown
- Select or search for specific session ID
- All traces with that session_id will be grouped together

**Via Python SDK:**
```python
from langfuse import Langfuse

langfuse = Langfuse(
    secret_key="sk-lf-...",
    public_key="pk-lf-..."
)

# Fetch traces from specific session
traces = langfuse.api.trace.list(
    session_id="chat-session-abc-123",
    limit=100
)

# Check session details
sessions = langfuse.api.session.list(
    limit=10
)
```

**Use Case Examples:**
- Find all traces from a single conversation thread
- Debug multi-turn conversations by viewing full session history
- Group related test scenarios together
- Track user journey across multiple interactions

---

### 2. Filter by User ID

**Via UI:**
- Click "User" filter in the Traces view
- Type or select the user ID
- View all traces associated with that user across all sessions

**Via Python SDK:**
```python
# Fetch all traces for a specific user
traces = langfuse.api.trace.list(
    user_id="user-john-doe",
    limit=100
)

# Get user's session list
user_sessions = langfuse.api.session.list(
    user_id="user-john-doe",
    limit=50
)
```

**Via REST API:**
```bash
curl -X GET "https://cloud.langfuse.com/api/public/traces?user_id=user-john-doe" \
  -H "Authorization: Basic $(echo -n 'pk:sk' | base64)"
```

**Use Case Examples:**
- Monitor individual user's agent interactions
- Identify patterns in specific user's behavior
- Cost tracking per user
- Investigate user-reported issues
- A/B testing by user cohorts

---

### 3. Filter by Metadata Fields

Metadata provides arbitrary JSON-structured data attached to traces and observations for enhanced filtering.

**Setting Metadata in Your Agent:**
```python
# In your LiveKit agent code (using OpenTelemetry)
from livekit.agents.telemetry import set_tracer_provider
from utils.telemetry import setup_observability

# When setting up observability, pass metadata
metadata = {
    "langfuse.session.id": room_name,
    "langfuse.user.id": user_id,
    "environment": "production",
    "agent_version": "1.2.0",
    "deployment_region": "us-west-2",
    "experiment_id": "exp-qualified-flow-v2"
}

trace_provider = setup_observability(metadata=metadata)
```

**Filtering by Metadata in UI:**
- Click "Metadata" filter
- Select key-value pairs to filter on
- Multiple metadata filters use AND logic (all must match)

**Filtering via Metrics API (Advanced):**
```python
from langfuse import Langfuse

langfuse = Langfuse(secret_key="sk-...", public_key="pk-...")

# Query traces with metadata filtering
query = {
    "view": "traces",
    "filters": [
        {
            "column": "metadata",
            "operator": "=",
            "key": "environment",
            "value": "production",
            "type": "stringObject"
        },
        {
            "column": "metadata",
            "operator": "contains",
            "key": "experiment_id",
            "value": "exp-",
            "type": "stringObject"
        }
    ],
    "fromTimestamp": "2024-10-01T00:00:00Z",
    "toTimestamp": "2024-10-31T23:59:59Z"
}

result = langfuse.api.metrics.metrics(query=query)
```

**Metadata Best Practices:**
- Merge all metadata in a single update (avoid multiple calls to the same key)
- Use dot notation for nested data: `{"feature.flags.silent_mode": true}`
- Keep metadata lightweight; don't duplicate trace data as metadata
- Structure consistently across all traces for reliable filtering

**Recommended Metadata Fields:**
```python
metadata = {
    # Feature flagging
    "feature_flags": {
        "silent_mode": False,
        "experimental_flow": True
    },

    # Deployment context
    "environment": "production",  # production, staging, dev
    "agent_version": "1.2.0",
    "deployment_id": "deploy-abc123",

    # Experiment tracking
    "experiment": "qualified-flow-v2",
    "variant": "variant-a",

    # Business context
    "customer_segment": "enterprise",
    "trial_phase": "week-2",

    # Request context
    "entry_point": "web",  # web, sip, api
    "consent_status": "given"
}
```

---

## 4. Full-Text Search (Find Specific Content)

**Via UI Search Box:**
- Use the search box at the top of the Traces view
- Enter keywords to search across trace inputs and outputs
- Searches case-insensitive token-based matching
- Results include traces containing the text

**Search Examples:**
```
"How do I integrate with Salesforce?"  # Find specific questions
"Unable to"                             # Find error-related conversations
"team of 10"                            # Find qualification signals
"schedule a demo"                       # Find conversion signals
```

**Full-Text Search Mechanics:**
- Uses ClickHouse's `hasTokenCaseInsensitive` function
- Searches trace input, output, and observation content
- Case-insensitive token matching
- Fast, indexed search across millions of traces

**Via SDK (Limited Support):**
- Direct full-text search via SDK not available
- Use UI for full-text search capabilities
- Can export traces and search locally if needed

**Use Case Examples:**
- Find conversations mentioning specific products
- Locate error messages in traces
- Search for specific user questions
- Find conversations with particular keywords (e.g., "contract", "pricing")

---

## 5. Filter by Trace Level & Type

**Filter Trace Properties:**
- **Level**: `DEFAULT`, `DEBUG`, `INFO`, `WARNING`, `ERROR`
- **Status**: Success, error, or other outcomes
- **Type**: Agent, generation, tool call, etc.

**Via UI:**
```
Level: ERROR              → Find all error traces
Name: "LLM Generation"    → Find specific operation types
Status: Failed            → Find failed operations
```

**Via Python SDK:**
```python
# Fetch error traces only
error_traces = langfuse.api.trace.list(
    level="ERROR",
    limit=50
)

# Fetch traces with specific name
llm_traces = langfuse.api.trace.list(
    name="llm_inference",
    limit=100
)
```

---

## 6. Filter by Tags

Tags are simple string values for organizing and categorizing traces.

**Setting Tags in Your Agent:**
```python
from livekit.agents.telemetry import set_tracer_provider

# Tags can be set when creating traces
@observe()
def my_function():
    langfuse_context.update_current_trace(
        tags=["production", "consent-given", "qualified"]
    )
```

**Via Python SDK:**
```python
# Filter traces with specific tags
qualified_traces = langfuse.api.trace.list(
    tags=["qualified"],
    limit=100
)

# Filter by multiple tags (AND logic - all tags must be present)
prod_qualified = langfuse.api.trace.list(
    tags=["production", "qualified"],
    limit=100
)
```

**Recommended Tag Strategy:**
```
Production Tags:
- "production"
- "staging"
- "development"

Feature/Experiment Tags:
- "silent-mode"
- "qualified-flow-v2"
- "experimental-tts"

Outcome Tags:
- "qualified"
- "unqualified"
- "consent-declined"
- "successful-handoff"

Data Quality Tags:
- "test-call"
- "incomplete"
- "truncated-audio"
```

**Tag Filtering Limitations:**
- Avoid special characters (`,` can break filtering)
- Filter returns traces with ALL specified tags (AND logic)
- Tags are append-only (cannot be removed)
- Designed for categories, not high-cardinality data

---

## 7. Filter by Errors

**Find Failed Traces:**

**Via UI:**
- Add filter: `Level: ERROR`
- View error details including stack traces
- See which component failed (STT, LLM, TTS, etc.)

**Via Python SDK:**
```python
# Get all error-level traces
errors = langfuse.api.trace.list(
    level="ERROR",
    limit=50
)

# Check error details
for error_trace in errors.data:
    print(f"Trace: {error_trace.id}")
    print(f"Error: {error_trace.output}")
    print(f"Timestamp: {error_trace.timestamp}")
```

**Common Error Patterns to Search:**
- Authentication failures (API key issues)
- TTS audio generation failures
- LLM timeout/rate limit errors
- Tool call failures (knowledge base search, calendar API, etc.)
- STT processing errors

---

## 8. Filter by Observation Type (Tool Calls, Functions)

**Searching for Specific Operations:**

**Via UI Filters:**
- Type: `GENERATION` → LLM calls only
- Type: `TOOL` → Tool/function calls only
- Type: `SPAN` → Custom operations
- Type: `CHAIN` → Multi-step workflows

**Via Python SDK:**
```python
# Get observations (steps within traces)
observations = langfuse.api.observations.get_many(
    type="TOOL",  # TOOL, GENERATION, SPAN, CHAIN, AGENT
    limit=100
)

# Get all generations (LLM calls)
llm_calls = langfuse.api.observations.get_many(
    type="GENERATION",
    limit=50
)

for obs in llm_calls.data:
    print(f"Model: {obs.model}")
    print(f"Input tokens: {obs.usage.input if obs.usage else 0}")
    print(f"Output: {obs.output}")
```

**Observation Types in Your Agent:**
```python
# Tool call (e.g., knowledge base search)
@observe(as_type="tool")
def search_knowledge_base(query):
    return search_results

# LLM generation
@observe(as_type="generation")
def call_llm(prompt):
    return llm_response

# Custom span for timing
@observe(as_type="span")
def custom_operation():
    pass
```

**Use Cases:**
- Analyze LLM token usage and costs
- Debug tool call failures
- Trace function execution paths
- Identify performance bottlenecks

---

## 9. Natural Language Filtering (Beta)

**NEW FEATURE**: Filter using plain English queries (Langfuse Cloud beta).

**Enable in UI:**
1. Go to Organization Settings
2. Enable "AI Features" (owner/admin only)
3. Uses AWS Bedrock with zero data retention

**Query Examples:**
```
"Find all default level traces with latency greater than 2 seconds"
"Show me traces with errors from production"
"Filter for traces with over 9000 tokens"
"Find traces from qualified users in the last 24 hours"
```

**How It Works:**
- Describe what you want in natural language
- Langfuse converts to appropriate filters
- You can refine if needed
- Privacy-first: AWS Bedrock, zero data retention

---

## 10. Time-Range Filtering

**Via UI:**
- Date picker in top right of Traces view
- Select: Last hour, Last 24h, Last 7 days, Last 30 days
- Or choose custom date range

**Via Python SDK:**
```python
from datetime import datetime, timedelta

# Traces from last 24 hours
start_time = datetime.now() - timedelta(hours=24)
recent_traces = langfuse.api.trace.list(
    from_timestamp=start_time.isoformat(),
    limit=100
)

# Specific date range for analysis
traces = langfuse.api.trace.list(
    from_timestamp="2024-10-01T00:00:00Z",
    to_timestamp="2024-10-31T23:59:59Z",
    limit=1000
)
```

---

## Best Practices for Organizing Traces

### 1. Use Hierarchical Naming

Structure trace names to enable filtering:
```
"agent/initialization"
"agent/turn/qualification"
"agent/turn/knowledge_search"
"agent/turn/llm_inference"
"agent/turn/tts_generation"
"agent/handoff"
```

### 2. Combine Session + User ID + Tags

```python
# At agent startup
metadata = {
    "langfuse.session.id": room_name,    # Groups related calls
    "langfuse.user.id": user_id,         # Links to user
}

# During execution
langfuse_context.update_current_trace(
    tags=[
        "qualified" if is_qualified else "unqualified",
        "consent-given",
        environment
    ]
)
```

### 3. Metadata for Dynamic Filtering

Instead of tags for high-cardinality data, use metadata:
```python
# DON'T do this (too many tags):
tags=[f"customer-{customer_id}", f"account-{account_id}"]

# DO this (use metadata):
metadata={
    "customer_id": customer_id,
    "account_id": account_id,
    "trial_status": "active",
    "team_size": 15
}
```

### 4. Attach Context to Observations

Include relevant context in each observation:
```python
with tracer.start_as_current_span("knowledge_search") as span:
    span.set_attribute("query", search_query)
    span.set_attribute("results_count", len(results))
    span.set_attribute("search_time_ms", elapsed_ms)
    # Search logic here
```

---

## Advanced: Programmatic Analysis

### Example: Cost Analysis by User

```python
from langfuse import Langfuse

langfuse = Langfuse(secret_key="...", public_key="...")

# Get traces with usage data
traces = langfuse.api.trace.list(limit=1000)

# Analyze costs
user_costs = {}
for trace in traces.data:
    user = trace.user_id or "unknown"
    if user not in user_costs:
        user_costs[user] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cost": 0.0
        }

    # Sum usage across all observations
    # (Langfuse handles cost calculation)
    if trace.costs:
        user_costs[user]["cost"] += trace.costs.total

# Report
for user, costs in sorted(user_costs.items(),
                          key=lambda x: x[1]["cost"],
                          reverse=True):
    print(f"{user}: ${costs['cost']:.2f}")
```

### Example: Error Rate by Agent Version

```python
query = {
    "view": "traces",
    "filters": [
        {
            "column": "metadata",
            "operator": "=",
            "key": "agent_version",
            "value": "1.2.0",
            "type": "stringObject"
        }
    ]
}

# Count errors vs total
all_traces = langfuse.api.trace.list(
    metadata={"agent_version": "1.2.0"},
    limit=10000
)

error_count = sum(
    1 for t in all_traces.data
    if t.level == "ERROR"
)
error_rate = (error_count / len(all_traces.data)) * 100
print(f"Error rate v1.2.0: {error_rate:.2f}%")
```

---

## Debugging Conversation Issues

### Scenario: User Reports Audio Quality Problem

**Search Strategy:**
```
1. Get session ID from user report
2. Filter: session_id="xyz"
3. Look at STT observations
   - Check audio_duration
   - Check transcription accuracy
4. Check TTS observations
   - Look for audio_duration mismatches
   - Check streaming latency (ttfb - time to first byte)
5. View metadata for audio settings
```

### Scenario: Agent Hung/No Response

**Search Strategy:**
```
1. Filter: user_id="abc" AND level="ERROR"
2. Look at most recent traces
3. Check for:
   - LLM timeout (generation took >10s)
   - Knowledge base search failure
   - Tool call error
4. Check timestamps between observations
   - Large gap = bottleneck there
```

### Scenario: Unqualified User Incorrectly Qualified

**Search Strategy:**
```
1. Filter: tags=["qualified", "unqualified"]
2. Look for traces with qualification step
3. Search text: "team size", "employees", etc.
4. Check metadata:
   - qualification_logic_version
   - qualification_score
5. View LLM generation span
   - Check prompt used
   - Check response tokens (reasoning)
```

---

## Integration with Your Agent

### Setting Up Search-Friendly Traces

In your LiveKit agent's telemetry setup:

```python
# my-app/src/utils/telemetry.py
def setup_observability(metadata: Optional[Dict[str, Any]] = None):
    """
    Configure LangFuse with searchable metadata.

    Args:
        metadata: Session context for filtering
            - langfuse.session.id: room_name or session identifier
            - langfuse.user.id: user identifier
            - Custom fields for filtering
    """
    # ... existing setup code ...

    # Add searchable metadata
    enriched_metadata = {
        "langfuse.session.id": metadata.get("langfuse.session.id"),
        "langfuse.user.id": metadata.get("langfuse.user.id"),
        "environment": os.getenv("DEPLOYMENT_ENV", "production"),
        "agent_version": "1.0.0",
        "stt_provider": "deepgram",
        "llm_model": "gpt-4-turbo-preview",
        "tts_provider": "cartesia",
    }

    set_tracer_provider(trace_provider, metadata=enriched_metadata)
```

### Adding Tags During Execution

```python
# In your agent turn handler
from livekit.agents import observe

@observe()
async def on_user_turn_complete(ctx: AgentSession):
    # Determine qualification state
    is_qualified = ctx.user_context.get("qualified", False)

    # Add searchable tags
    langfuse_context.update_current_trace(
        tags=[
            "qualified" if is_qualified else "unqualified",
            "consent_given" if ctx.consent_given else "consent_pending"
        ],
        metadata={
            "qualification_score": ctx.qualification_score,
            "qualification_reason": ctx.qualification_reason,
            "turn_number": ctx.turn_count,
            "user_sentiment": ctx.detected_sentiment
        }
    )
```

---

## Troubleshooting Common Search Issues

### Issue: Can't Find Recent Traces
**Solution:** LangFuse has 15-30 second ingestion delay
- Wait before searching
- Check agent logs to confirm traces are being sent
- Verify LANGFUSE_* environment variables are set

### Issue: Metadata Filtering Not Working
**Solution:** Metadata must be set before trace completes
```python
# ✅ Correct: Set metadata early
langfuse_context.update_current_trace(metadata={...})

# ❌ Wrong: Set metadata after span ends
# (metadata may not be captured)
```

### Issue: Tags Filter Returns No Results
**Solution:** Check for special characters in tag values
- Don't use commas (`,`) in tags
- Use underscore or hyphen separators instead
- Verify tag was actually added in traces

### Issue: Can't Find Traces by Metadata
**Solution:** Use Metrics API for complex metadata queries
```python
# Instead of trying to filter in list()
# Use metrics endpoint for aggregation
query = {...}
result = langfuse.api.metrics.metrics(query=query)
```

---

## Quick Reference: API Methods

| Task | Method | Notes |
|------|--------|-------|
| List all traces | `langfuse.api.trace.list()` | Supports filters, pagination |
| Get single trace | `langfuse.api.trace.get(trace_id)` | Full trace with observations |
| List sessions | `langfuse.api.session.list()` | Group traces by conversation |
| List observations | `langfuse.api.observations.get_many()` | Individual steps in trace |
| Filter by metadata | `metrics.metrics(query=...)` | Use Metrics API for complex queries |
| Update current trace | `langfuse_context.update_current_trace()` | Add tags, metadata, user_id |

---

## Additional Resources

- **Langfuse Documentation**: https://langfuse.com/docs/
- **Query Traces Guide**: https://langfuse.com/docs/query-traces
- **Sessions Documentation**: https://langfuse.com/docs/tracing-features/sessions
- **Tags Documentation**: https://langfuse.com/docs/tracing-features/tags
- **Metadata Documentation**: https://langfuse.com/docs/tracing-features/metadata
- **Observation Types**: https://langfuse.com/docs/observability/features/observation-types
- **Natural Language Filtering**: https://langfuse.com/changelog/2025-09-30-natural-language-filters

---

**Last Updated**: October 31, 2024
**Context**: PandaDoc Voice AI Trial Success Agent (LiveKit + LangFuse integration)

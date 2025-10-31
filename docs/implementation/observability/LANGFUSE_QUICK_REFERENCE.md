# Langfuse Search & Filtering - Quick Reference

Fast lookup guide for common search patterns in Langfuse.

## UI Search Quick Tips

| What to Find | Filter/Search | Location |
|--------------|---|----------|
| **Specific conversation** | Session dropdown | Traces > Filters |
| **All user's traces** | User filter | Traces > Filters > User |
| **Errors only** | Level: ERROR | Traces > Filters > Level |
| **Recent issues** | Last 24h time filter | Traces > Date picker |
| **Text mentions** | Search box (e.g., "Salesforce") | Top of Traces |
| **Tool calls** | Type: TOOL | Traces > Filters > Type |
| **LLM calls** | Type: GENERATION | Traces > Filters > Type |
| **Tagged traces** | Tags: ["qualified"] | Traces > Filters > Tags |
| **Production only** | Tags: ["production"] | Traces > Filters > Tags |

---

## Python SDK Quick Snippets

### Get traces from a conversation session
```python
traces = langfuse.api.trace.list(session_id="room-123", limit=100)
```

### Get all traces from a user
```python
user_traces = langfuse.api.trace.list(user_id="user-john", limit=100)
```

### Get error traces
```python
errors = langfuse.api.trace.list(level="ERROR", limit=50)
```

### Get tool call observations
```python
tools = langfuse.api.observations.get_many(type="TOOL", limit=50)
```

### Get LLM generations (token usage, costs)
```python
llm_calls = langfuse.api.observations.get_many(type="GENERATION", limit=50)
for call in llm_calls.data:
    print(f"Tokens: {call.usage.total}, Cost: {call.usage.cost}")
```

### Get traces from last 24 hours
```python
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(hours=24)).isoformat()
recent = langfuse.api.trace.list(from_timestamp=yesterday, limit=100)
```

---

## Trace Anatomy for Searching

When debugging, understand what's searchable:

```
TRACE (searchable fields)
├── id (unique)
├── session_id ← Filter here!
├── user_id ← Filter here!
├── tags ← Filter here! (use sparingly)
├── metadata ← Filter here! (use Metrics API)
├── level (DEFAULT, DEBUG, INFO, WARNING, ERROR) ← Filter here!
├── timestamps (created_at, updated_at) ← Filter here!
└── input/output (full text searchable) ← Full-text search!
    │
    └── OBSERVATION (span, generation, tool, etc.)
        ├── name
        ├── type (GENERATION, TOOL, SPAN, CHAIN, etc.)
        ├── input (searchable)
        ├── output (searchable)
        ├── duration
        └── usage (tokens, cost for generations)
```

---

## Metadata vs Tags

**Use TAGS for:** Small set of categorical labels (10-100 values)
- Examples: `["production", "qualified", "consent-given"]`
- Limitation: No commas, no special chars
- Benefit: Fast filtering in UI

**Use METADATA for:** Detailed context, high-cardinality data
- Examples: `{"customer_id": "cust-123", "trial_phase": "week-2", "sentiment": "positive"}`
- Benefit: Can store JSON structures, more flexible filtering
- Limitation: Use Metrics API for complex queries

---

## Common Debugging Flows

### "Agent hung for user X"
1. Filter: `user_id=X`
2. Check most recent trace
3. Look at SPAN observations
4. Find where duration jumps (that's the bottleneck)

### "Qualification logic broken"
1. Filter: `tags=["unqualified"]`
2. Check recent traces
3. View LLM GENERATION span
4. Check prompt and reasoning

### "User says audio cuts off"
1. Get `session_id` from user
2. Filter: `session_id=xyz`
3. View TTS observations
4. Check `audio_duration` and `ttfb` (time to first byte)
5. Check STT observations
6. Check metadata for audio settings

### "Cost is too high"
1. Filter: `user_id=expensive-user`
2. Get GENERATION observations
3. Sum `completion_tokens` × cost per token
4. Compare LLM model versions

---

## Setting Up Traces for Easy Finding

In your LiveKit agent code:

```python
# Set session and user early
langfuse_context.update_current_trace(
    session_id=room_name,      # ← required for grouping
    user_id=user_id,            # ← required for user analysis
)

# Add tags for categorization
langfuse_context.update_current_trace(
    tags=[
        "qualified" if qualified else "unqualified",
        "production",
        "consent-given"
    ]
)

# Add rich metadata for filtering
langfuse_context.update_current_trace(
    metadata={
        "customer_segment": "enterprise",
        "entry_point": "web",
        "tts_model": "cartesia-sonic-2",
        "qualification_score": 8.5,
        "turn_count": 3
    }
)
```

---

## Observation Type Cheat Sheet

| Type | What | How to Find |
|------|------|-----------|
| **GENERATION** | LLM calls | `type=GENERATION` filter |
| **TOOL** | Function/API calls | `type=TOOL` filter |
| **SPAN** | Timing blocks | `type=SPAN` filter |
| **CHAIN** | Multi-step workflows | `type=CHAIN` filter |
| **AGENT** | Agent decision points | `type=AGENT` filter |
| **RETRIEVER** | Knowledge base queries | `type=RETRIEVER` filter |

---

## Filter Operators (Metrics API)

When using Metrics API for advanced queries:

```python
{
    "column": "metadata",
    "operator": "=",           # Equals
    "key": "environment",
    "value": "production",
    "type": "stringObject"
}

# Other operators:
# ">" for numeric (latency > 2000ms)
# "contains" for substring matching
# "in" for multiple values
```

---

## Langfuse Limits & Gotchas

| Limitation | Workaround |
|-----------|-----------|
| Metadata filtered via UI can be slow | Use Metrics API for complex queries |
| Tags with special chars (`,`) don't filter | Avoid special chars in tags |
| Data available after 15-30s delay | Don't search immediately after trace |
| Can't remove tags (append-only) | Plan tags carefully |
| High-cardinality metadata (1M+ unique values) | Use structured metadata keys |

---

## Dashboard Navigation

**To find Langfuse UI:**
1. Go to https://cloud.langfuse.com (or your hosted instance)
2. Select Project
3. Click "Traces" in left sidebar
4. Use filters and search box

**Common views:**
- **Traces**: All individual request traces
- **Sessions**: Grouped conversations
- **Users**: All users and their interactions
- **Logs**: Detailed debug logs
- **Metrics**: Aggregated performance data

---

## Integration with LiveKit Agent

Your telemetry setup enables Langfuse searches:

**File**: `/my-app/src/utils/telemetry.py`

The `setup_observability()` function configures OpenTelemetry to export to Langfuse.
Pass metadata dict to enable session/user/environment filtering:

```python
from utils.telemetry import setup_observability

trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": room_name,
        "langfuse.user.id": user_id,
        "environment": "production"
    }
)
```

---

## Getting Started with Langfuse Searches

1. **First trace**: Deploy agent, make test call, wait 30s
2. **Find it**: Filters > User > select test user
3. **Explore**: Click on trace to see full execution flow
4. **Add tags**: Click "Add tag" on trace for quick filtering
5. **Export**: Use SDK to programmatically fetch for analysis

---

## Useful API Endpoints

| Endpoint | Use Case |
|----------|----------|
| `/api/public/traces` | List traces with filters |
| `/api/public/sessions` | Get session info |
| `/api/public/observations` | Get trace steps |
| `/api/public/metrics` | Aggregated metrics and analytics |
| `/api/public/users` | User tracking data |

---

## Links

- **Langfuse Dashboard**: https://cloud.langfuse.com
- **Query Traces Docs**: https://langfuse.com/docs/query-traces
- **Sessions Docs**: https://langfuse.com/docs/tracing-features/sessions
- **Observation Types**: https://langfuse.com/docs/observability/features/observation-types
- **Metrics API**: https://langfuse.com/docs/metrics/features/metrics-api

---

**See also:** `LANGFUSE_SEARCH_FILTERING_GUIDE.md` for detailed examples and best practices.

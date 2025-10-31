# Langfuse Search & Filtering Research Summary

## Overview

Comprehensive research on Langfuse's search and filtering capabilities for finding, debugging, and analyzing traces in the PandaDoc Voice AI agent. This document summarizes key findings and provides actionable guidance.

---

## 1. Session ID Search & Filtering

### Capability
Search and group traces by conversation session using session IDs.

### Implementation
- **UI**: Filters dropdown → Session ID field
- **SDK**: `langfuse.api.trace.list(session_id="xyz")`
- **Auto-grouping**: All traces with same session_id grouped together

### Use Cases
- Find complete conversation history
- Debug multi-turn interactions
- Group related test scenarios
- Track user journey

### Status
✅ **Fully Implemented** - Core feature, highly optimized

---

## 2. User ID Search & Filtering

### Capability
Filter all traces associated with a specific user across all sessions.

### Implementation
- **UI**: Filters → User field
- **SDK**: `langfuse.api.trace.list(user_id="user-123")`
- **REST API**: `GET /api/public/traces?user_id=user-123`

### Features
- User overview dashboard (token usage, trace count, feedback)
- Individual user profiles at `/project/{id}/users/{userId}`
- Cost tracking per user
- User segmentation and cohort analysis

### Status
✅ **Fully Implemented** - Well-documented, widely used

---

## 3. Metadata Field Filtering

### Capability
Filter by arbitrary JSON metadata attached to traces and observations.

### Implementation
```python
# Setting metadata
langfuse_context.update_current_trace(
    metadata={
        "environment": "production",
        "trial_phase": "week-2",
        "qualification_score": 8.5
    }
)

# Filtering via Metrics API
query = {
    "view": "traces",
    "filters": [{
        "column": "metadata",
        "operator": "=",
        "key": "environment",
        "value": "production",
        "type": "stringObject"
    }]
}
result = langfuse.api.metrics.metrics(query=query)
```

### Advantages
- Flexible JSON structure
- Supports nested data
- Complex filtering via Metrics API

### Limitations
- UI metadata filtering can be slow
- Complex OTel metadata can make filtering difficult
- Requires Metrics API for advanced queries

### Status
✅ **Available but Complex** - Recently enhanced (Oct 2025), Metrics API recommended for complex queries

---

## 4. Full-Text Search

### Capability
Search across trace input/output content for specific text strings.

### Implementation
- **UI**: Search box in Traces view
- **Method**: Case-insensitive token-based matching
- **Backend**: Uses ClickHouse's `hasTokenCaseInsensitive`

### Use Cases
```
Search for: "How do I integrate with Salesforce?"  (specific questions)
Search for: "Unable to"                             (error patterns)
Search for: "team of 10"                            (qualification signals)
Search for: "contract signed"                       (conversion signals)
```

### Status
✅ **Fully Implemented** - Fast and reliable

---

## 5. Filtering by Observation Type (Tool Calls, Functions)

### Capability
Find specific types of operations: GENERATION, TOOL, SPAN, CHAIN, AGENT, etc.

### Implementation
```python
# Get all tool calls
tools = langfuse.api.observations.get_many(type="TOOL", limit=100)

# Get all LLM calls
llm_calls = langfuse.api.observations.get_many(type="GENERATION", limit=100)

# Check specific observation details
for obs in llm_calls.data:
    print(f"Model: {obs.model}")
    print(f"Duration: {obs.duration}")
    print(f"Tokens: {obs.usage.total if obs.usage else 0}")
```

### Observation Types
| Type | Purpose |
|------|---------|
| GENERATION | LLM calls (prompts, completions, tokens) |
| TOOL | Function/API calls (weather, calendar, KB search) |
| SPAN | Custom timing blocks |
| CHAIN | Multi-step workflows |
| AGENT | Agent decision points |
| RETRIEVER | Knowledge base queries |
| EVENT | Discrete tracking points |
| EMBEDDING | Embedding generation |

### Status
✅ **Fully Implemented** - Well-supported across SDKs

---

## 6. Error Filtering

### Capability
Find and debug failed traces by filtering on error level.

### Implementation
```python
# UI: Level filter → ERROR
# SDK: langfuse.api.trace.list(level="ERROR", limit=50)

# Trace levels: DEFAULT, DEBUG, INFO, WARNING, ERROR
```

### What's Captured
- Error messages and stack traces
- Component failures (STT, LLM, TTS, tools)
- Timeouts and rate limits
- API failures

### Status
✅ **Fully Implemented** - Core feature

---

## 7. Tag-Based Filtering & Organization

### Capability
Organize traces with categorical string tags for quick filtering.

### Implementation
```python
# Setting tags
langfuse_context.update_current_trace(
    tags=["production", "qualified", "consent-given"]
)

# Filtering by tags
traces = langfuse.api.trace.list(
    tags=["qualified"],  # Returns traces with this tag
    limit=100
)

# Multiple tags (AND logic - all must be present)
traces = langfuse.api.trace.list(
    tags=["production", "qualified"],
    limit=100
)
```

### Recommended Tags
```
Environment:     production, staging, development
Features:        silent-mode, experimental-tts, qualified-flow-v2
Outcomes:        qualified, unqualified, consent-declined, successful-handoff
Quality:         test-call, incomplete, truncated-audio
```

### Limitations
- Avoid commas and special characters
- No tag removal (append-only)
- AND logic for multiple tags (not OR)
- Not suitable for high-cardinality data (use metadata instead)

### Status
✅ **Implemented but with Gotchas** - Works well for 10-100 distinct values

---

## 8. Natural Language Filtering (Beta)

### Capability
Filter traces using plain English queries powered by AWS Bedrock.

### Implementation
- **Availability**: Langfuse Cloud beta
- **Privacy**: Zero data retention (AWS Bedrock)
- **Enable**: Organization Settings → AI Features

### Query Examples
```
"Find all default level traces with latency greater than 2 seconds"
"Show me traces with errors from production"
"Filter for traces with over 9000 tokens"
"Find conversations from last 24 hours with qualification"
```

### Status
🆕 **Beta Feature** - Recently released (Sept 2025), privacy-first approach

---

## 9. Best Practices for Organizing Traces

### Recommended Structure
```
TRACE (top-level grouping)
├── session_id ← "room-abc-123"
├── user_id ← "user-john"
├── tags ← ["qualified", "production"]
├── metadata ← {details about context}
└── observations
    ├── LLM call (GENERATION)
    ├── Knowledge search (TOOL)
    ├── TTS (SPAN)
    └── Custom timing (SPAN)
```

### Key Principles
1. **Set session_id early** - Enables conversation grouping
2. **Add user_id** - Links to user analytics
3. **Use tags carefully** - 10-100 distinct values max
4. **Rich metadata** - Use for detailed context
5. **Hierarchical naming** - Structure trace names: `agent/turn/llm_inference`

### Metadata vs Tags Decision
| Choose TAGS if | Choose METADATA if |
|---|---|
| < 100 distinct values | > 100 distinct values |
| Fast UI filtering needed | Complex filtering needed |
| Simple categories | Detailed context |
| No special characters | JSON structures okay |

---

## 10. Integration with LiveKit & OpenTelemetry

### Current Integration
- **File**: `/my-app/src/utils/telemetry.py`
- **Method**: OpenTelemetry → OTLP → Langfuse
- **Export**: BatchSpanProcessor with batching (2048 queue, 512 batch)

### Metadata Passing
```python
def setup_observability(metadata: Optional[Dict[str, Any]] = None):
    """
    Args:
        metadata: Session context dict
            - langfuse.session.id: room_name
            - langfuse.user.id: user_id
            - Custom fields for filtering
    """
    # Configuration happens here
```

### Recommended Integration Pattern
```python
# 1. Setup with basic context
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": room_name,
        "langfuse.user.id": user_id,
        "environment": "production",
        "agent_version": "1.0.0"
    }
)

# 2. Add dynamic data during execution
langfuse_context.update_current_trace(
    tags=["qualified" if qualified else "unqualified"],
    metadata={
        "qualification_score": score,
        "turn_count": turn_number
    }
)

# 3. Flush on shutdown
ctx.add_shutdown_callback(lambda: trace_provider.force_flush())
```

---

## 11. Advanced Querying & Analysis

### Metrics API
For aggregated queries (costs, usage, patterns):
```python
query = {
    "view": "traces",
    "filters": [...],
    "fromTimestamp": "2024-10-01T00:00:00Z",
    "toTimestamp": "2024-10-31T23:59:59Z"
}
result = langfuse.api.metrics.metrics(query=query)
```

### SDK Queries
For individual trace analysis:
```python
# Fetch and analyze
traces = langfuse.api.trace.list(
    user_id="user-123",
    from_timestamp=yesterday,
    limit=1000
)

# Process results
total_cost = sum(t.costs.total for t in traces.data if t.costs)
error_count = sum(1 for t in traces.data if t.level == "ERROR")
```

### Programmatic Patterns
- Cost analysis by user/segment
- Error rate tracking by version
- Performance metrics extraction
- Custom reporting and dashboards

---

## 12. Common Debugging Workflows

### Workflow 1: User Reports Issue
1. Get session_id from user
2. Filter: `session_id=xyz`
3. View trace timeline
4. Check observations for bottlenecks
5. Search output for error messages

### Workflow 2: Agent Not Responding
1. Filter: `user_id=abc` AND `level=ERROR`
2. Check most recent trace
3. Look at span durations
4. Find where duration jumps (bottleneck)
5. Analyze that observation (LLM? Tool? TTS?)

### Workflow 3: Qualification Logic Issue
1. Filter: `tags=["unqualified"]`
2. View recent traces
3. Check LLM GENERATION observation
4. Review prompt and reasoning tokens
5. Adjust qualification logic if needed

---

## 13. Known Limitations & Workarounds

| Limitation | Workaround |
|---|---|
| 15-30s ingestion delay | Don't search immediately after trace |
| Complex metadata filtering slow | Use Metrics API for aggregates |
| Tags with special chars fail | Use hyphens/underscores instead |
| Can't remove tags | Plan tag strategy carefully |
| High-cardinality metadata slow | Keep metadata keys under 1M values |
| Direct metadata filter in list API recent | Metrics API for complex queries |

---

## 14. Data Ingestion & Availability

### Timeline
- **Capture**: Real-time as trace executes
- **Send**: Batched every ~30 seconds
- **Available**: 15-30 seconds after completion
- **Searchable**: Within 1-2 minutes for full-text

### Best Practices
- Don't expect traces immediately after completion
- Wait 30+ seconds before searching
- Use logs for immediate debugging
- Use Langfuse for post-analysis

---

## 15. Recommended Implementation for Your Agent

### Phase 1: Basic Tracing (Week 1)
- ✅ Enable OpenTelemetry → Langfuse
- ✅ Set session_id (room_name)
- ✅ Set user_id
- ✅ Verify traces appear in UI
- ✅ Test session/user filtering

### Phase 2: Debugging Enhancement (Week 2)
- ✅ Add tags for qualification states
- ✅ Add metadata for trial phase, segment
- ✅ Add turn_count, sentiment to metadata
- ✅ Test filtering by tags and metadata
- ✅ Create debugging workflows

### Phase 3: Analytics (Week 3+)
- ✅ Setup cost analysis by user
- ✅ Track error rates by version
- ✅ Monitor LLM token usage
- ✅ Create custom dashboards
- ✅ Export data for further analysis

---

## Key Takeaways

### What Works Well
✅ Session/user ID filtering (extremely fast and reliable)
✅ Full-text search (good for finding content)
✅ Tag-based organization (simple categories)
✅ Observation type filtering (reliable)
✅ Error-level filtering (comprehensive)

### What Needs Attention
⚠️ Metadata filtering (use Metrics API for complex queries)
⚠️ Tag special characters (avoid commas and special chars)
⚠️ Data availability latency (wait 30s for full search capability)
⚠️ High-cardinality metadata (avoid >1M distinct values)

### Best Practices
1. Always set session_id and user_id
2. Use tags for major categories (< 100 values)
3. Use metadata for detailed context
4. Plan tag strategy before implementation
5. Use full-text search for finding content
6. Use Metrics API for aggregated analysis
7. Wait for data availability before searching
8. Test new filtering strategies in console mode

---

## Resources & Links

### Official Langfuse
- **Docs**: https://langfuse.com/docs/
- **Query Traces**: https://langfuse.com/docs/query-traces
- **Sessions**: https://langfuse.com/docs/tracing-features/sessions
- **Users**: https://langfuse.com/docs/tracing-features/users
- **Tags**: https://langfuse.com/docs/tracing-features/tags
- **Metadata**: https://langfuse.com/docs/tracing-features/metadata
- **Observations**: https://langfuse.com/docs/observability/features/observation-types
- **Natural Language Filtering**: https://langfuse.com/changelog/2025-09-30-natural-language-filters

### Your Codebase
- **Telemetry Setup**: `/my-app/src/utils/telemetry.py`
- **Agent Integration**: `/my-app/src/agent.py`
- **LiveKit Docs**: https://docs.livekit.io/ (use LiveKit MCP server)

---

## Documentation Generated

1. **LANGFUSE_SEARCH_FILTERING_GUIDE.md** - Comprehensive reference guide
2. **LANGFUSE_QUICK_REFERENCE.md** - Fast lookup cheat sheet
3. **LANGFUSE_DOCUMENTATION_INDEX.md** - Navigation and learning paths
4. **This document** - Research summary and findings

---

## Next Steps

1. **Read**: LANGFUSE_SEARCH_FILTERING_GUIDE.md (Sections 1-4)
2. **Practice**: Use Langfuse UI to filter test traces
3. **Setup**: Add session_id/user_id to agent code
4. **Test**: Verify filtering works with real traces
5. **Expand**: Add metadata and tags as needed
6. **Analyze**: Use SDK to programmatically analyze traces

---

**Research Date**: October 31, 2024
**Scope**: Langfuse search and filtering capabilities
**Status**: Complete and comprehensive
**Confidence**: High - based on official Langfuse documentation and code review

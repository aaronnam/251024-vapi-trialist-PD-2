# LLM Span Input Enrichment for Langfuse

## Problem Statement
The `llm_node` spans in Langfuse were showing `Input: null` instead of displaying the conversation context sent to the LLM. This made it impossible to understand what conversation history prompted each LLM response.

## Root Cause
LiveKit creates `llm_node` spans internally when LLM requests are made, but these spans only include timing and cost metrics by default. The actual conversation messages sent to the LLM are not automatically captured in the span attributes, so Langfuse had no `langfuse.input` attribute to display.

This is similar to the `user_speaking` span issue that was previously fixed, where LiveKit created spans with only timing attributes.

## Solution Approach
We enriched the LLM spans with conversation context using a two-part solution:

### Part 1: Conversation History Formatter
Created a helper function that formats the `ChatContext` into a readable conversation log:

**Location**: `/src/agent.py` lines 1191-1259

```python
def format_conversation_history(chat_context) -> str:
    """
    Format ChatContext into a readable conversation log for Langfuse.

    Extracts messages from LiveKit's ChatContext and formats them as:

    system: You are Sarah, a Trial Success Specialist...

    user: Hello, I need help with PandaDoc

    assistant: Hi! I'd be happy to help you with PandaDoc...

    user: How do I integrate with Salesforce?
    """
```

**Key Features**:
- Handles multiple content types (string, list, ChatContent objects)
- Graceful error handling to prevent agent failures
- Readable format for Langfuse UI
- Extracts text from complex content structures

### Part 2: Span Enrichment in LLMMetrics Handler
Updated the `metrics_collected` event handler to enrich LLM spans when metrics are emitted:

**Location**: `/src/agent.py` lines 1465-1496

```python
if isinstance(ev.metrics, LLMMetrics):
    # ... existing cost tracking code ...

    # Enrich LLM span with conversation context
    try:
        from opentelemetry import trace as otel_trace

        # Format conversation history
        conversation_input = format_conversation_history(session.history)

        # Get current span (should be llm_node)
        current_span = otel_trace.get_current_span()

        if current_span and current_span.is_recording():
            # Set Langfuse-specific attributes
            current_span.set_attribute("langfuse.input", conversation_input)
            current_span.set_attribute("llm.messages.count", message_count)
            current_span.set_attribute("llm.prompt_tokens", ev.metrics.prompt_tokens)
            current_span.set_attribute("llm.completion_tokens", ev.metrics.completion_tokens)

            logger.debug(f"✅ Enriched LLM span with {message_count} messages")
    except Exception as e:
        logger.warning(f"Failed to enrich LLM span: {e}")
```

**Why This Works**:
1. **Timing**: The `metrics_collected` event fires after the LLM request completes, when the span is still active
2. **Context Access**: We have access to `session.history` which contains all conversation messages
3. **Span Access**: `otel_trace.get_current_span()` returns the active `llm_node` span
4. **Langfuse Integration**: The `langfuse.input` attribute is recognized by Langfuse and displayed in the UI

## Expected Behavior After Fix

### Before Fix
```
llm_node span:
  Input: null
  Output: "Great! Thanks for that. I'm here to help..."
  Metadata: tokens, timing, cost
```

### After Fix
```
llm_node span:
  Input:
    system: You are Sarah, a Trial Success Specialist...

    user: Hello, I need help with PandaDoc

    assistant: Hi! I'd be happy to help you with PandaDoc...

    user: How do I integrate with Salesforce?

  Output: "To integrate PandaDoc with Salesforce..."
  Metadata: tokens, timing, cost, message count
```

## Deployment History

### Version: v20251031055350
- **Deployed**: 2025-10-31 05:54:52 UTC
- **Changes**:
  - Added `format_conversation_history()` helper function
  - Updated `_on_metrics_collected()` to enrich LLM spans with conversation input
  - Added debug logging for span enrichment success

## Verification Steps

1. **Create a Test Session**
   - Open Agent Playground
   - Start a new conversation
   - Have a multi-turn dialogue with the agent

2. **Check Langfuse Dashboard**
   - Navigate to the session trace
   - Find the `llm_node` spans
   - Verify the "Input" field shows the conversation history
   - Check that the format is readable (role: content pairs)

3. **Verify Span Attributes**
   Each `llm_node` span should now include:
   - ✅ `langfuse.input` - Full conversation history
   - ✅ `llm.messages.count` - Number of messages in context
   - ✅ `llm.prompt_tokens` - Input tokens used
   - ✅ `llm.completion_tokens` - Output tokens used

4. **Check Agent Logs**
   ```bash
   lk agent logs | grep "Enriched LLM span"
   ```
   Should see messages like:
   ```
   ✅ Enriched LLM span with 5 messages (234 prompt tokens, 89 completion tokens)
   ```

## Troubleshooting

### Issue: LLM span still shows null input
**Possible Causes**:
1. Looking at old sessions created before deployment
2. Agent not restarted after deployment
3. Span enrichment failing (check logs for warnings)

**Resolution**:
- Only test with NEW sessions created after v20251031055350
- Verify agent version: `lk agent status`
- Check logs for enrichment errors: `lk agent logs | grep -i "failed to enrich"`

### Issue: Conversation history is truncated
**Possible Cause**: Very long conversations might be truncated by Langfuse or OpenTelemetry

**Resolution**:
- This is expected behavior for extremely long conversations
- Consider adding truncation logic to the formatter if needed
- The `llm.messages.count` attribute still shows the full count

### Issue: Formatting errors in conversation history
**Possible Cause**: Complex or unexpected message content types

**Resolution**:
- Check logs for "Error formatting conversation history" warnings
- The formatter includes comprehensive error handling and fallbacks
- Report specific content structures that cause issues for improvement

## Technical Notes

### Why We Enrich in metrics_collected
- The `LLMMetrics` event fires after each LLM request completes
- At this point, the `llm_node` span is still active and recording
- We have access to the full conversation history via `session.history`
- The span can still accept new attributes via `set_attribute()`

### Relationship to user_speaking Fix
This fix follows the same pattern as the `user_speaking` span enrichment:
1. Identify when LiveKit creates an internal span
2. Access the active span via OpenTelemetry
3. Enrich it with relevant attributes for Langfuse
4. Use fallback strategies for robustness

### Performance Considerations
- **Formatting Cost**: Simple string concatenation, negligible impact
- **Memory**: Conversation history already in memory, just reformatted
- **Latency**: Happens after LLM request completes, doesn't affect response time
- **Error Handling**: Wrapped in try-catch to prevent agent failures

### Alternative Approaches Considered

#### 1. Create Custom LLM Spans
**Rejected**: Would create duplicate spans alongside LiveKit's internal spans, causing confusion in traces.

#### 2. Hook into conversation_item_added Events
**Rejected**: These events fire when items are added, not when LLM requests are made. Would miss the timing window.

#### 3. Access Internal _llm_node_span
**Rejected**: LiveKit doesn't expose this internal reference like it does for `_user_speaking_span`. Using `get_current_span()` is more reliable.

## Related Documentation
- [USER_TRANSCRIPT_FIX.md](./USER_TRANSCRIPT_FIX.md) - Similar fix pattern for user_speaking spans
- [LANGFUSE_INTEGRATION_REVIEW.md](./LANGFUSE_INTEGRATION_REVIEW.md) - Overall Langfuse integration review
- [LiveKit Agents Telemetry](https://docs.livekit.io/agents/build/metrics/) - Official telemetry documentation

## Future Enhancements

### Potential Improvements
1. **Truncation Strategy**: Add intelligent truncation for very long conversations
2. **Message Filtering**: Option to exclude system messages from display
3. **Timestamp Enrichment**: Add message timestamps if available
4. **Token Prediction**: Show estimated vs actual token counts
5. **Output Enrichment**: Also enrich with the actual LLM response text (not just conversation input)

### Known Limitations
1. **Output Not Captured**: Currently only enriching input, not the LLM's generated output
2. **Single-Turn Focus**: Best for conversation-based agents, not batch processing
3. **Format Fixed**: Conversation format is hardcoded, not customizable per use case

## Conclusion
The LLM span enrichment fix provides full visibility into the conversation context sent to the LLM for each request. This is essential for:
- **Debugging**: Understanding why the LLM generated specific responses
- **Optimization**: Identifying when conversation context is too long or repetitive
- **Cost Analysis**: Correlating conversation complexity with token usage
- **Quality Assurance**: Verifying that conversation history is being managed correctly

This fix completes the Langfuse integration by ensuring both user inputs (`user_speaking` spans) and LLM context (`llm_node` spans) are visible in traces.
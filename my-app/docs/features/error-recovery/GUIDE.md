# Error Recovery Implementation Guide

This guide documents the comprehensive error recovery infrastructure implemented for the PandaDocTrialistAgent voice AI system.

## Overview

The error recovery system ensures the voice agent maintains natural conversation flow even when underlying services fail. It implements production-quality patterns including:

- **Circuit Breaker Pattern**: Prevents cascading failures and protects struggling services
- **Exponential Backoff Retries**: Handles transient errors gracefully
- **Natural Language Error Responses**: Voice-optimized error messages that maintain conversation flow
- **State Preservation**: Maintains conversation context despite failures

## Architecture

### Components

1. **`error_recovery.py`** - Core infrastructure module
   - `CircuitBreaker`: Implements circuit breaker pattern
   - `retry_with_exponential_backoff()`: Retry logic with exponential backoff
   - `ErrorRecoveryMixin`: Provides error response generation and state preservation

2. **`agent.py`** - Integration with PandaDocTrialistAgent
   - Helper methods for tool error handling
   - Circuit breakers for external services
   - Example tool implementations

3. **`tests/test_error_recovery.py`** - Comprehensive test suite
   - 22 tests covering all error recovery scenarios
   - Integration tests demonstrating end-to-end behavior

## Usage Patterns

### 1. Circuit Breaker for External Services

Use circuit breakers to protect against cascading failures when calling external APIs:

```python
result = await self.call_with_retry_and_circuit_breaker(
    service_name="amplitude",  # Service identifier
    func=lambda: fetch_amplitude_data(user_id),
    fallback_response="I'll continue without that data for now.",
    max_retries=2  # Voice-optimized: short retry count
)

if isinstance(result, str):
    # Fallback response was returned - service unavailable
    return result
else:
    # Normal response with data
    return f"Found data: {result}"
```

**How it works:**
- Circuit opens after 3 consecutive failures (configurable)
- Stays open for 30 seconds (configurable recovery timeout)
- Transitions to half-open, then closes on successful call
- While open, immediately returns fallback without calling service

### 2. Tool Error Handling with State Preservation

Wrap tool implementations with error recovery to maintain conversation state:

```python
@function_tool()
async def lookup_user_data(
    self,
    context: RunContext,
    user_id: str,
) -> str:
    """Look up user data from CRM."""
    return await self.handle_tool_with_error_recovery(
        context=context,
        tool_name="lookup_user_data",
        tool_func=lambda: self._fetch_crm_data(user_id),
        error_type="connection_issue"  # Determines error message style
    )
```

**Benefits:**
- Automatic state snapshot before tool execution
- State restoration on failure
- Natural language error responses (not technical)
- Maintains conversation context

### 3. Timeout Protection for Long-Running Operations

Protect against hanging operations with timeouts:

```python
async def _fetch_crm_data(self, user_id: str) -> dict:
    """Internal method with timeout protection."""
    try:
        result = await asyncio.wait_for(
            api_call(user_id),
            timeout=5.0  # Voice-optimized: short timeout
        )
        return result
    except asyncio.TimeoutError as e:
        raise asyncio.TimeoutError(f"CRM lookup timed out") from e
```

### 4. Natural Language Error Responses

Get voice-optimized error messages for any failure scenario:

```python
# In a tool that encounters an error
error_msg = self.get_error_response("connection_issue")
raise ToolError(error_msg)
```

**Available error types:**
- `"tool_failure"` - "Let me try finding that information another way."
- `"connection_issue"` - "I'm experiencing a brief connection issue. Bear with me for just a second."
- `"timeout"` - "That's taking longer than expected. Let me try a quicker approach."
- `"service_unavailable"` - "That service appears to be temporarily unavailable. Let's continue without it for now."
- `"data_not_found"` - "I couldn't find that information. Can you clarify what you're looking for?"
- `"generic"` - "I encountered an issue, but I'm still here to help. What else can I do for you?"

Each type has multiple variants that are randomly selected to keep conversations natural.

## Configuration

### Circuit Breakers

Circuit breakers are initialized in the agent's `__init__` method:

```python
self.circuit_breakers: dict[str, CircuitBreaker] = {
    "amplitude": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
    "salesforce": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
    "chilipiper": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
    "hubspot": CircuitBreaker(failure_threshold=3, recovery_timeout=30.0),
}
```

**Parameters:**
- `failure_threshold`: Number of consecutive failures before opening (default: 3)
- `recovery_timeout`: Seconds to wait before trying again (default: 30.0)

### Retry Configuration

Retry behavior is optimized for voice AI with shorter delays:

```python
result = await retry_with_exponential_backoff(
    func=api_call,
    max_retries=2,      # Fewer retries for voice (default: 3)
    base_delay=0.5,     # Shorter initial delay (default: 1.0)
    max_delay=3.0,      # Shorter max delay (default: 10.0)
    jitter=True         # Randomize delays to prevent thundering herd
)
```

**Voice AI Optimization:**
- Shorter delays minimize conversational pauses
- Fewer retries reduce user wait time
- Jitter prevents synchronized retries across multiple agents

## Example Tools

Two example tools demonstrate the patterns:

### 1. Timeout Handling Example

```python
@function_tool()
async def example_tool_with_timeout(
    self,
    context: RunContext,
    query: str,
) -> str:
    """Example tool showing timeout handling."""
    return await self.handle_tool_with_error_recovery(
        context=context,
        tool_name="example_tool_with_timeout",
        tool_func=lambda: self._example_long_running_query(query),
        error_type="timeout",
    )
```

### 2. Circuit Breaker Example

```python
@function_tool()
async def example_tool_with_circuit_breaker(
    self,
    context: RunContext,
    user_id: str,
) -> str:
    """Example tool showing circuit breaker usage."""
    result = await self.call_with_retry_and_circuit_breaker(
        service_name="amplitude",
        func=lambda: self._fetch_example_user_data(user_id),
        fallback_response="I'll continue helping you without that user data.",
        max_retries=2,
    )

    if isinstance(result, str):
        return result  # Fallback response
    return f"Found user data: {result}"  # Normal response
```

## Testing

Run the comprehensive test suite:

```bash
# Run all error recovery tests
uv run pytest tests/test_error_recovery.py -v

# Run specific test
uv run pytest tests/test_error_recovery.py::test_circuit_breaker_opens_after_threshold -v

# Run with coverage
uv run pytest tests/test_error_recovery.py --cov=src.error_recovery --cov=src.agent
```

**Test Coverage:**
- Circuit breaker state transitions (closed → open → half-open → closed)
- Retry logic with exponential backoff
- Natural language error response generation
- State preservation during failures
- Tool error handling patterns
- End-to-end integration scenarios

## Implementation Checklist

When implementing a new tool with error recovery:

- [ ] Wrap tool logic in `handle_tool_with_error_recovery()`
- [ ] Add timeout protection for long-running operations
- [ ] Use circuit breaker for external service calls
- [ ] Choose appropriate error type for error messages
- [ ] Add circuit breaker to agent's `__init__` if new service
- [ ] Write tests for success, failure, and timeout scenarios
- [ ] Verify conversation state is preserved on errors
- [ ] Test with LiveKit session error handler integration

## Production Considerations

### Monitoring

Log circuit breaker state changes and failures:

```python
# Circuit breaker logs automatically:
logger.info("Circuit breaker: Service recovered, closing circuit")
logger.warning("Circuit breaker: Opening circuit after 3 failures")
logger.info("Circuit breaker: Transitioning to half-open state")
```

Monitor these logs to detect:
- Frequently opening circuits (service instability)
- Circuits stuck open (persistent outages)
- High retry rates (transient network issues)

### Tuning Parameters

Adjust based on observed behavior:

1. **Circuit Breaker**:
   - Increase `failure_threshold` if transient errors are common
   - Decrease `recovery_timeout` for faster recovery attempts
   - Increase `recovery_timeout` to reduce load on struggling services

2. **Retries**:
   - Reduce `max_retries` for faster failure response
   - Increase `base_delay` if backend needs more recovery time
   - Disable `jitter` for predictable behavior (testing only)

### Session-Level Error Handling

The agent integrates with LiveKit's session error handler:

```python
@session.on("error")
async def _on_error(event):
    """Handle errors during the agent session."""
    error = event.error
    source = event.source

    if error.recoverable:
        # Automatic retry - log for monitoring
        logger.info(f"Recoverable {source} error: {error}")
    else:
        # Unrecoverable - inform user gracefully
        agent = session.agent
        if isinstance(agent, PandaDocTrialistAgent):
            error_msg = agent.get_error_response("service_unavailable")
            await session.say(
                f"{error_msg} I apologize for the interruption."
            )
```

## Best Practices

1. **Always preserve state**: Use `handle_tool_with_error_recovery()` to snapshot state before risky operations

2. **Choose appropriate error types**: Match error type to user-facing message needs

3. **Optimize for voice**: Keep retries fast (max 2-3), delays short (< 3s max)

4. **Fail gracefully**: Always provide fallback responses or alternative paths

5. **Log appropriately**:
   - Warning for recoverable errors
   - Error for unrecoverable failures
   - Info for state transitions

6. **Test failure scenarios**: Write tests that simulate failures, not just happy paths

7. **Monitor circuit breakers**: Track which services fail frequently

8. **Voice-first design**: Error messages should sound natural when spoken

## Future Enhancements

Potential improvements to consider:

- **Adaptive timeouts**: Learn optimal timeout values from historical data
- **Circuit breaker metrics**: Export to monitoring systems (Prometheus, Datadog)
- **Fallback chains**: Try multiple services in order of preference
- **Graceful degradation**: Reduce feature set instead of failing completely
- **User notification**: Inform users proactively when services are degraded
- **Rate limiting**: Protect services from excessive retry load
- **Bulkhead pattern**: Isolate failures to prevent cross-service contamination

## References

- LiveKit Error Handling Docs: https://docs.livekit.io/agents/build/events
- LiveKit Tool Documentation: https://docs.livekit.io/agents/build/tools
- Circuit Breaker Pattern: https://martinfowler.com/bliki/CircuitBreaker.html
- Retry Patterns: https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/

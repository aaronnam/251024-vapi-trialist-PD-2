# Error Recovery & Fault Tolerance

**Status**: ✅ Implemented and tested
**Last Updated**: October 27, 2025

## Overview

Comprehensive production-quality error recovery infrastructure that enables the PandaDoc Voice Agent to maintain natural conversation flow even when underlying services fail.

This feature implements proven patterns for building reliable systems:
- **Circuit Breaker Pattern**: Prevents cascading failures across service dependencies
- **Exponential Backoff Retries**: Gracefully handles transient errors
- **Natural Language Responses**: Maintains conversation flow during failures
- **State Preservation**: Keeps conversation context intact despite errors

## Documentation

### [GUIDE.md](./GUIDE.md)
**Complete implementation guide and usage patterns**

- Usage examples and implementation patterns
- Circuit breaker configuration
- Integration with agent tools
- Best practices for production
- Comprehensive code examples

**Use when**: Implementing error handling in agent tools or learning production patterns

### [IMPLEMENTATION.md](./IMPLEMENTATION.md)
**Implementation details and completion status**

- What was implemented and when
- Architecture of error recovery components
- Core components and their roles
- Key features and capabilities
- Test coverage

**Use when**: Understanding the implementation details or reviewing what's been completed

## Key Features

### Circuit Breaker Pattern
```
Protects failing services from cascading failures
├── Opens after N consecutive failures
├── Auto-recovers after timeout
├── Prevents storm of requests to struggling service
└── Allows service time to recover
```

### Exponential Backoff Retries
```
Handles transient failures gracefully
├── Retries with increasing delays
├── Adds jitter to prevent thundering herd
├── Configurable max retries
└── Distinguishes transient vs permanent failures
```

### Natural Error Responses
```
Maintains conversation flow during failures
├── Voice-optimized error messages
├── Non-technical user-friendly language
├── Suggests alternatives when possible
└── Preserves conversation context
```

## Implementation Components

### Core Module: `error_recovery.py`
- `CircuitBreaker` class - Circuit breaker implementation
- `retry_with_exponential_backoff()` - Retry decorator
- `ErrorRecoveryMixin` - Mixin for error handling in agents

### Agent Integration: `agent.py`
- Error recovery mixin integration
- Circuit breakers for external services
- Tool error handling patterns
- Example implementations

### Tests: `tests/test_error_recovery.py`
- 22+ comprehensive tests
- Circuit breaker behavior verification
- Retry logic validation
- Integration scenarios
- 100% test pass rate

## Quick Start

### For Tool Developers
When implementing a tool that calls external services:

```python
# Use circuit breaker for external service calls
result = await self.call_with_retry_and_circuit_breaker(
    service_name="amplitude",
    service_call=lambda: amplitude_client.track(event),
    fallback_response="I'll note that for later"
)
```

### For Error Responses
Keep responses natural and conversational:

```python
# Natural error response
"Sorry, I'm having trouble connecting right now. Let me try again in a moment."

# NOT technical
"CircuitBreakerOpen: Amplitude service unavailable"
```

## Architecture Diagram

```
Tool Call
    ↓
Circuit Breaker Check
    ├─ Open? → Return fallback + error response
    ├─ Half-open? → Try request
    └─ Closed? → Continue
    ↓
Retry Logic
    ├─ Success? → Return result
    ├─ Transient error? → Exponential backoff + retry
    └─ Permanent error? → Error response + fallback
    ↓
State Preservation
    └─ Maintain conversation context regardless
```

## Configuration

Default settings (can be customized):

```python
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 3      # Failures to trigger open
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30      # Seconds before half-open
RETRY_MAX_ATTEMPTS = 3                      # Retry attempts
RETRY_BASE_DELAY = 0.5                      # Seconds
RETRY_MAX_DELAY = 30                        # Max backoff delay
```

## Related Documentation

- **Implementation Details**: [IMPLEMENTATION.md](./IMPLEMENTATION.md)
- **Usage Guide**: [GUIDE.md](./GUIDE.md)
- **Development Guide**: [../../AGENTS.md](../../AGENTS.md)
- **Feature Index**: [../README.md](../README.md)

## Testing

All error recovery patterns are covered by comprehensive tests:
- `test_circuit_breaker_opens_after_failures()`
- `test_circuit_breaker_half_open_recovery()`
- `test_exponential_backoff_retry()`
- `test_error_recovery_with_fallback()`
- And 18+ more...

Run tests:
```bash
uv run pytest tests/test_error_recovery.py -v
```

## Production Checklist

Before deploying to production:
- [ ] Review GUIDE.md for your use case
- [ ] Configure circuit breaker thresholds for your services
- [ ] Test error responses sound natural in conversation
- [ ] Verify fallback responses are appropriate
- [ ] Run test suite: `uv run pytest`
- [ ] Load test to verify behavior under pressure

## Key Takeaways

✅ **Prevents cascading failures** - One service failure doesn't crash your agent
✅ **Graceful degradation** - Agent continues conversation despite errors
✅ **Production-ready** - 22+ tests, proven patterns
✅ **Configurable** - Tune thresholds for your services
✅ **Extensible** - Easy to add error handling to new tools

---

**Last Updated**: October 29, 2025
**Status**: ✅ Production Ready

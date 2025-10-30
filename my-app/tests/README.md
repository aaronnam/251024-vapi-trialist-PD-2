# PandaDoc Agent Testing Suite

## Overview

This directory contains a comprehensive testing framework for the PandaDoc Trial Success Voice Agent, following LiveKit's testing best practices.

## Test Files

### Core Test Suite
- **`test_pandadoc_comprehensive.py`** - Main comprehensive test suite with 19 tests covering:
  - Consent protocol compliance
  - Knowledge base search behavior
  - Lead qualification detection
  - Sales meeting booking logic
  - Instruction adherence
  - Error recovery
  - Conversation flows

### Existing Tests
- **`test_agent.py`** - Basic agent behavior tests
- **`test_calendar_booking_tool.py`** - Calendar integration tests
- **`test_error_recovery.py`** - Error handling tests
- **`test_unleash_tool.py`** - Knowledge base search tests

### Documentation
- **`TESTING_GUIDE.md`** - Complete testing instructions and best practices
- **`TEST_PROMPTS_CATALOG.md`** - Exhaustive catalog of test prompts organized by category
- **`README.md`** - This file

## Quick Start

### Running Tests

```bash
# Run all comprehensive tests
uv run pytest tests/test_pandadoc_comprehensive.py -v

# Run specific test categories
uv run pytest -k "consent"         # Consent protocol tests
uv run pytest -k "qualification"   # Lead qualification tests
uv run pytest -k "search"          # Knowledge base search tests
uv run pytest -k "booking"         # Sales booking tests

# Run with verbose output for debugging
LIVEKIT_EVALS_VERBOSE=1 uv run pytest -s

# Run a single test
uv run pytest tests/test_pandadoc_comprehensive.py::test_consent_accepted_flow
```

### Manual Testing

```bash
# Start console mode for interactive testing
uv run python src/agent.py console

# Use prompts from TEST_PROMPTS_CATALOG.md for systematic testing
```

## Test Coverage Areas

### 1. Consent Protocol (CRITICAL)
- ✅ Affirmative consent handling
- ✅ Consent decline handling
- ✅ Consent questions and clarification
- ✅ Ambiguous response handling

### 2. Knowledge Base Search
- ✅ No search for greetings/chat
- ✅ Search for PandaDoc questions
- ✅ Error handling when search fails

### 3. Lead Qualification
- ✅ Team size detection (5+ users)
- ✅ Document volume detection (100+ docs/month)
- ✅ Integration needs (Salesforce, HubSpot, API)

### 4. Sales Meeting Booking
- ✅ Qualified users can book
- ✅ Unqualified users directed to self-serve
- ✅ Email handling

### 5. Instruction Adherence
- ✅ Stays in PandaDoc domain
- ✅ No hallucination on features
- ✅ Voice-optimized responses

### 6. Conversation Flows
- ✅ Discovery to qualification
- ✅ Friction rescue mode
- ✅ Multi-turn conversations

### 7. Error Recovery
- ✅ Circuit breaker behavior
- ✅ Service failure handling
- ✅ Graceful degradation

## Test Design Philosophy

### Elegant Simplicity
- **Focus on behavior, not implementation** - Tests validate what the agent does, not how
- **Use LLM judge for intent** - Verify meaning rather than exact wording
- **Mock external dependencies** - Test agent logic in isolation
- **Fast feedback loops** - Most tests complete in < 2 seconds

### Comprehensive Coverage
- **Critical paths first** - Consent, qualification, and booking logic
- **Edge cases included** - Ambiguous inputs, service failures
- **Voice-specific tests** - Conciseness, interruption handling

### Not Over-Engineered
- **Simple test structure** - Arrange, Act, Assert pattern
- **Minimal dependencies** - Uses LiveKit's built-in testing framework
- **Clear intent descriptions** - Each test has obvious purpose
- **Pragmatic assertions** - Balance between strict and flexible

## Using the Test Prompts Catalog

The `TEST_PROMPTS_CATALOG.md` contains 200+ test prompts organized into 10 categories:

1. **Consent Protocol** - 20+ variations
2. **Qualification Discovery** - 40+ scenarios
3. **Knowledge Base Search** - 30+ queries
4. **Sales Meeting Booking** - 15+ requests
5. **Instruction Adherence** - 20+ edge cases
6. **Error Recovery** - 10+ failure modes
7. **Conversation Flows** - 10+ multi-turn
8. **Voice Optimization** - 10+ voice-specific
9. **Edge Cases** - 20+ unusual requests
10. **Security/Safety** - 15+ security probes

### Systematic Testing Process

1. Start with consent tests (legal compliance)
2. Test qualification detection (business logic)
3. Verify tool usage (cost management)
4. Check conversation flows (user experience)
5. Probe edge cases (robustness)
6. Test security boundaries (safety)

## Current Test Results

As of the last run:
- ✅ **12 tests passing** - Core functionality working
- ❌ **7 tests failing** - Need investigation or agent adjustment

Common failure patterns:
- Agent may search when not expected (cost consideration)
- Qualification signals may need tuning
- Some edge cases may reveal implementation gaps

## Debugging Failed Tests

### Enable verbose output
```bash
LIVEKIT_EVALS_VERBOSE=1 uv run pytest tests/test_pandadoc_comprehensive.py::test_that_failed -s
```

### Test manually in console
```bash
uv run python src/agent.py console
# Enter the exact prompt from the failing test
```

### Check mock behavior
Add print statements in mock functions to see what's being called

## Next Steps

### For Initial Testing
1. Run the comprehensive suite
2. Review failures to understand agent behavior
3. Decide: fix agent or adjust tests?

### For Continuous Testing
1. Add tests before new features (TDD)
2. Run tests before deployment
3. Update TEST_PROMPTS_CATALOG.md with new scenarios

### For Production
1. Set up CI/CD with GitHub Actions
2. Add pre-commit hooks for critical tests
3. Monitor test coverage metrics

## Best Practices

### DO ✅
- Test behavior, not exact wording
- Use the test prompts catalog systematically
- Mock external services for speed
- Keep tests independent and fast
- Add new test cases as bugs are found

### DON'T ❌
- Test implementation details
- Make tests dependent on network
- Write vague intent descriptions
- Skip edge case testing
- Deploy without running tests

## Questions?

- See `TESTING_GUIDE.md` for detailed instructions
- Check `TEST_PROMPTS_CATALOG.md` for test scenarios
- Review failing tests to understand agent behavior
- Use console mode for interactive debugging
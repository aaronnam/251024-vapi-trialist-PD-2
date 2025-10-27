# LiveKit Agents Testing Framework & Best Practices

## Executive Summary

LiveKit Agents provides a comprehensive testing framework for voice AI agents built on pytest and async/await patterns. The framework supports:

1. **AgentSession testing** - Simulated agent conversations without running a full server
2. **LLM mocking** - Using real LLMs or mocks for evaluation
3. **Evaluation framework** - Judge-based assertions using LLM-powered evaluation
4. **Function tool testing** - Direct testing of agent tools
5. **Async test patterns** - pytest-asyncio integration with proper fixture scoping
6. **TDD approach** - Recommended for core agent behavior changes

---

## 1. Test Structure and Setup Patterns

### 1.1 Project Configuration

**File:** `pyproject.toml`

```toml
[dependency-groups]
dev = [
    "pytest",
    "pytest-asyncio",
    "ruff",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

**Key Settings:**
- `asyncio_mode = "auto"` - Automatically marks async functions as async tests
- `asyncio_default_fixture_loop_scope = "function"` - Creates new event loop per test

### 1.2 Test Directory Structure

```
my-app/
├── src/
│   ├── agent.py           # Main agent implementation
│   └── __init__.py
├── tests/
│   └── test_agent.py      # All tests for the agent
├── pyproject.toml
└── .env.local             # Test credentials
```

**Running Tests:**
```bash
uv run pytest                    # Run all tests
uv run pytest tests/test_agent.py -v  # Run specific file with verbose output
uv run pytest -k test_offers    # Run tests matching pattern
```

---

## 2. AgentSession Testing with Mock LLMs

### 2.1 Basic Test Structure Pattern

**From:** `/my-app/tests/test_agent.py`

```python
import pytest
from livekit.agents import AgentSession, inference, llm
from agent import Assistant


def _llm() -> llm.LLM:
    """Create LLM instance for testing."""
    return inference.LLM(model="openai/gpt-4.1-mini")


@pytest.mark.asyncio
async def test_offers_assistance() -> None:
    """Evaluation of the agent's friendly nature."""
    # Setup: Create LLM and session context managers
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        # Initialize agent with the session
        await session.start(Assistant())
        
        # Run a single turn with user input
        result = await session.run(user_input="Hello")
        
        # Verify response using evaluation framework
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the user in a friendly manner.
                
                Optional context that may or may not be included:
                - Offer of assistance with any request the user may have
                - Other small talk or chit chat is acceptable
                """,
            )
        )
        
        # Ensure no unexpected events
        result.expect.no_more_events()
```

### 2.2 AgentSession API Reference

```python
# Initialize session
session = AgentSession(
    llm="openai/gpt-4.1-mini",      # LLM model
    stt="assemblyai/universal-streaming:en",  # Speech-to-text (optional for testing)
    tts="cartesia/sonic-2:...",     # Text-to-speech (optional for testing)
    turn_detection=None,             # Turn detection (optional for testing)
    vad=None,                        # Voice activity detection (optional)
)

# Start session with agent
await session.start(agent_instance)

# Run single turn and get result
result = await session.run(user_input="Your question here")

# Assertion API
result.expect.next_event()      # Expect next event
result.expect.no_more_events()  # Expect no further events
```

### 2.3 LLM Creation Strategies

#### Using Real LLM for Testing (Requires API Keys)

```python
def _llm() -> llm.LLM:
    """Use real OpenAI model for comprehensive evaluation."""
    return inference.LLM(model="openai/gpt-4.1-mini")
```

**Pros:** Accurate evaluation, uses actual LLM reasoning
**Cons:** Slow, costs money, requires API key, non-deterministic

#### Using Local/Mock LLM (Recommended for CI/CD)

```python
from unittest.mock import Mock, AsyncMock

@pytest.fixture
async def mock_llm():
    """Create mock LLM for fast testing."""
    llm = Mock()
    llm.__aenter__ = AsyncMock(return_value=llm)
    llm.__aexit__ = AsyncMock(return_value=None)
    return llm
```

**Pros:** Fast, free, deterministic
**Cons:** Less realistic evaluation

#### Hybrid Approach

```python
import os

def _llm() -> llm.LLM:
    """Use real LLM in CI, mock in development."""
    if os.getenv("CI") == "true":
        # Fast mock in CI
        return create_mock_llm()
    else:
        # Real LLM in development for debugging
        return inference.LLM(model="openai/gpt-4.1-mini")
```

---

## 3. Function Tool Testing Strategies

### 3.1 Testing Function Tools in Isolation

```python
@pytest.mark.asyncio
async def test_weather_tool_integration():
    """Test that agent correctly uses weather tool."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = Assistant()
        await session.start(agent)
        
        # Trigger function that should call the weather tool
        result = await session.run(user_input="What's the weather in NYC?")
        
        # Verify function tool was called
        # (This depends on tool capturing or response analysis)
        await result.expect.next_event().is_message(role="assistant")
```

### 3.2 Mocking External Dependencies in Tools

```python
from unittest.mock import patch, AsyncMock

@pytest.mark.asyncio
async def test_tool_with_external_api():
    """Test tool that calls external API."""
    # Mock the external API
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Set up mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "location": "NYC",
            "temperature": 72,
            "description": "sunny"
        })
        mock_get.return_value.__aenter__.return_value = mock_response
        
        async with (
            _llm() as llm,
            AgentSession(llm=llm) as session,
        ):
            agent = Assistant()
            await session.start(agent)
            
            result = await session.run(user_input="Weather?")
            await result.expect.next_event().is_message(role="assistant")
```

### 3.3 Direct Tool Testing Pattern

```python
@pytest.mark.asyncio
async def test_tool_directly():
    """Test tool function directly without session."""
    from livekit.agents import RunContext
    from unittest.mock import Mock
    
    # Create agent instance
    agent = Assistant()
    
    # Create mock RunContext
    mock_context = Mock(spec=RunContext)
    mock_context.session = Mock()
    
    # Call tool directly
    try:
        result = await agent.my_tool(mock_context, param="test")
        assert result == expected_value
    except ToolError as e:
        assert "expected error message" in str(e)
```

---

## 4. Voice Pipeline Testing Approaches

### 4.1 Testing STT/TTS Pipeline (Optional Components)

```python
@pytest.mark.asyncio
async def test_voice_pipeline():
    """Test with STT and TTS components."""
    async with (
        _llm() as llm,
        AgentSession(
            llm=llm,
            stt="assemblyai/universal-streaming:en",  # Include STT
            tts="cartesia/sonic-2:...",              # Include TTS
        ) as session,
    ):
        await session.start(Assistant())
        
        # Test with text input (simulates STT output)
        result = await session.run(user_input="Hello")
        
        # Verify response (would be sent to TTS)
        await result.expect.next_event().is_message(role="assistant")
```

### 4.2 Testing Turn Detection

```python
@pytest.mark.asyncio
async def test_turn_detection():
    """Test turn detection for speaker changes."""
    from livekit.plugins.turn_detector.multilingual import MultilingualModel
    
    async with (
        _llm() as llm,
        AgentSession(
            llm=llm,
            turn_detection=MultilingualModel(),  # Enable turn detection
        ) as session,
    ):
        await session.start(Assistant())
        
        # Multiple turns simulating conversation
        result1 = await session.run(user_input="First message")
        await result1.expect.next_event().is_message(role="assistant")
        
        result2 = await session.run(user_input="Follow up question")
        await result2.expect.next_event().is_message(role="assistant")
```

---

## 5. Integration Testing Patterns

### 5.1 Multi-Turn Conversation Testing

```python
@pytest.mark.asyncio
async def test_multi_turn_conversation():
    """Test full conversation flow."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # First turn: greeting
        result1 = await session.run(user_input="Hello")
        await result1.expect.next_event().is_message(role="assistant")
        result1.expect.no_more_events()
        
        # Second turn: question
        result2 = await session.run(user_input="What can you help with?")
        await result2.expect.next_event().is_message(role="assistant")
        result2.expect.no_more_events()
        
        # Third turn: complex request
        result3 = await session.run(
            user_input="Tell me something interesting about AI"
        )
        await result3.expect.next_event().is_message(role="assistant")
        result3.expect.no_more_events()
```

### 5.2 Testing Agent Handoffs

```python
@pytest.mark.asyncio
async def test_handoff_to_specialized_agent():
    """Test handoff between agents."""
    from agent import Assistant, BillingAgent
    
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        main_agent = Assistant()
        await session.start(main_agent)
        
        # Trigger condition that causes handoff
        result = await session.run(user_input="I need billing support")
        
        # Verify handoff occurred (depends on implementation)
        event = await result.expect.next_event()
        # Could be: task delegation, agent handoff, etc.
```

### 5.3 Testing Workflow/Task Delegation

```python
@pytest.mark.asyncio
async def test_email_collection_task():
    """Test task-based workflow."""
    from livekit.agents.beta.workflows import GetEmailTask
    
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = Assistant()
        await session.start(agent)
        
        # Start email collection task
        result = await session.run(user_input="Please collect my email")
        
        # Verify task interaction
        await result.expect.next_event().is_message(role="assistant")
```

---

## 6. Test Fixtures and Utilities

### 6.1 Common Test Fixtures

```python
import pytest
from livekit.agents import AgentSession, inference, llm
from agent import Assistant


@pytest.fixture
async def llm_instance():
    """Shared LLM instance for tests."""
    async with inference.LLM(model="openai/gpt-4.1-mini") as llm:
        yield llm


@pytest.fixture
async def agent_session(llm_instance):
    """Shared agent session for tests."""
    async with AgentSession(llm=llm_instance) as session:
        yield session


@pytest.fixture
async def running_agent(agent_session):
    """Agent already started and ready for interaction."""
    await agent_session.start(Assistant())
    yield agent_session
```

### 6.2 Reusable Test Utilities

```python
# test_utils.py

import pytest
from livekit.agents import AgentSession


class TestResult:
    """Wrapper for test result assertions."""
    
    def __init__(self, result):
        self._result = result
    
    async def assert_message(self, role="assistant"):
        """Assert response is a message."""
        await (
            self._result.expect.next_event()
            .is_message(role=role)
        )
    
    async def assert_judged(self, llm, intent):
        """Assert response meets intent."""
        await (
            self._result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent=intent)
        )
    
    async def assert_no_more(self):
        """Assert no more events."""
        self._result.expect.no_more_events()


async def run_agent_test(session, user_input):
    """Helper to run test and wrap result."""
    result = await session.run(user_input=user_input)
    return TestResult(result)
```

### 6.3 Parameterized Tests

```python
@pytest.mark.parametrize("user_input,expected_intent", [
    ("Hello", "greets user in friendly manner"),
    ("What's the weather?", "should ask for location or provide weather"),
    ("I need help", "offers assistance"),
])
@pytest.mark.asyncio
async def test_various_inputs(user_input, expected_intent):
    """Test agent with various inputs."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        result = await session.run(user_input=user_input)
        
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent=expected_intent)
        )
        
        result.expect.no_more_events()
```

---

## 7. Evaluation Framework Usage

### 7.1 Judge-Based Evaluation

The `.judge()` method uses the LLM to evaluate agent responses against intent descriptions:

```python
@pytest.mark.asyncio
async def test_offers_assistance() -> None:
    """Evaluation of the agent's friendly nature."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        result = await session.run(user_input="Hello")
        
        # Judge evaluates if response matches intent
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Greets the user in a friendly manner.
                
                Optional context that may or may not be included:
                - Offer of assistance with any request the user may have
                - Other small talk or chit chat is acceptable, so long as it is friendly and not too intrusive
                """,
            )
        )
        
        result.expect.no_more_events()
```

### 7.2 Complex Evaluation Examples

```python
@pytest.mark.asyncio
async def test_grounding() -> None:
    """Evaluation of the agent's ability to refuse to answer."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        result = await session.run(user_input="What city was I born in?")
        
        # Evaluate refusal appropriately
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="""
                Does not claim to know or provide the user's birthplace information.
                
                The response should not:
                - State a specific city where the user was born
                - Claim to have access to the user's personal information
                - Provide a definitive answer about the user's birthplace
                
                The response may include various elements such as:
                - Explaining lack of access to personal information
                - Saying they don't know
                - Offering to help with other topics
                - Friendly conversation
                - Suggestions for sharing information
                """,
            )
        )
        
        result.expect.no_more_events()
```

### 7.3 Writing Effective Judge Prompts

**Guidelines for `.judge()` intent parameter:**

1. **Be specific about requirements:**
   - What MUST be in the response
   - What MUST NOT be in the response

2. **Allow flexibility:**
   - Use "may include" for optional elements
   - Specify "core requirement" for essentials

3. **Provide context:**
   - Explain why the evaluation matters
   - Give examples of acceptable variations

4. **Avoid over-specification:**
   - Don't require exact wording
   - Allow alternative phrasings

**Example - Good Prompt:**
```python
intent="""
The agent should demonstrate knowledge of Python.

Required:
- Must mention at least one Python feature or use case
- Should not contain factually incorrect Python information

Optional:
- Examples of Python code
- Comparison to other languages
- Links to Python resources
"""
```

**Example - Poor Prompt:**
```python
intent="Agent should talk about Python"  # Too vague
```

---

## 8. Pytest Patterns for Async Agents

### 8.1 Async Test Basics

```python
import pytest


@pytest.mark.asyncio
async def test_async_operation():
    """Basic async test with pytest-asyncio."""
    result = await some_async_function()
    assert result == expected


# Alternative without decorator (with asyncio_mode="auto")
async def test_async_operation_auto_mode():
    """Works automatically with asyncio_mode='auto'."""
    result = await some_async_function()
    assert result == expected
```

### 8.2 Context Manager Testing

```python
@pytest.mark.asyncio
async def test_context_manager():
    """Test with async context managers."""
    async with AsyncResource() as resource:
        # Resource is properly initialized
        result = await resource.do_something()
        assert result is not None
    # Resource is properly cleaned up


@pytest.mark.asyncio
async def test_multiple_context_managers():
    """Test with multiple nested context managers."""
    async with (
        Manager1() as mgr1,
        Manager2() as mgr2,
    ):
        result = await mgr1.combine_with(mgr2)
        assert result is correct
```

### 8.3 Event Loop and Fixture Scoping

```python
# pyproject.toml configuration
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"  # New loop per test
```

**Loop scoping options:**
- `"function"` - New loop for each test (recommended for isolation)
- `"class"` - Shared loop for class methods
- `"module"` - Shared loop for module
- `"session"` - Shared loop for entire session (careful with state)

```python
# Use function-scoped fixtures for clean state
@pytest.fixture
async def session():
    """Per-test session (new event loop)."""
    async with AgentSession(llm=_llm()) as session:
        yield session
```

### 8.4 Error Handling in Async Tests

```python
@pytest.mark.asyncio
async def test_error_handling():
    """Test that errors are raised correctly."""
    with pytest.raises(ToolError):
        async with AgentSession(llm=_llm()) as session:
            await session.start(BrokenAgent())
            result = await session.run(user_input="This should fail")


@pytest.mark.asyncio
async def test_timeout_handling():
    """Test timeout behavior."""
    import asyncio
    
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(
            slow_async_operation(),
            timeout=0.1
        )
```

---

## 9. Mock Objects and Test Utilities

### 9.1 Mocking RunContext

```python
from unittest.mock import Mock, AsyncMock
from livekit.agents import RunContext


def create_mock_run_context():
    """Create mock RunContext for tool testing."""
    context = Mock(spec=RunContext)
    context.session = Mock()
    context.session.userdata = {}
    context.speech_handle = Mock()
    context.function_call = Mock()
    
    # Mock async methods
    context.wait_for_playout = AsyncMock()
    context.disallow_interruptions = Mock()
    
    return context
```

### 9.2 Mocking External Services

```python
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_with_mocked_api():
    """Test tool with mocked external API."""
    with patch('aiohttp.ClientSession') as mock_session:
        mock_get = AsyncMock()
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"status": "success"}
        )
        mock_session.return_value.get = mock_get
        
        async with (
            _llm() as llm,
            AgentSession(llm=llm) as session,
        ):
            await session.start(Assistant())
            result = await session.run(user_input="Call external API")
            await result.expect.next_event().is_message(role="assistant")
```

### 9.3 Recording and Replaying Responses

```python
# responses.py
import json


class ResponseRecorder:
    """Record and replay test responses."""
    
    def __init__(self, filename):
        self.filename = filename
        self.responses = {}
    
    def record(self, key, response):
        """Record a response."""
        self.responses[key] = response
        with open(self.filename, 'w') as f:
            json.dump(self.responses, f)
    
    def replay(self, key):
        """Get recorded response."""
        with open(self.filename) as f:
            responses = json.load(f)
        return responses.get(key)


# Usage in tests
@pytest.fixture
def response_recorder():
    """Provide response recorder for tests."""
    return ResponseRecorder("test_responses.json")
```

---

## 10. Conversation Testing Patterns

### 10.1 State Verification in Conversations

```python
@pytest.mark.asyncio
async def test_conversation_state():
    """Test that agent maintains conversation context."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # First message
        result1 = await session.run(user_input="My name is Alice")
        response1 = await result1.expect.next_event().is_message(role="assistant")
        
        # Second message - should remember name
        result2 = await session.run(user_input="What's my name?")
        response2 = await result2.expect.next_event().is_message(role="assistant")
        
        # Judge that response includes the name
        await response2.judge(
            llm,
            intent="Correctly recalls the user's name as Alice"
        )
```

### 10.2 Tool Call Verification

```python
@pytest.mark.asyncio
async def test_tool_is_called():
    """Verify agent calls appropriate tool."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = Assistant()
        
        # Track tool calls
        original_tool = agent.lookup_weather
        call_count = 0
        
        async def tracked_tool(context, location):
            nonlocal call_count
            call_count += 1
            return await original_tool(context, location)
        
        agent.lookup_weather = tracked_tool
        
        await session.start(agent)
        result = await session.run(user_input="What's the weather in NYC?")
        
        assert call_count > 0, "Weather tool should have been called"
```

---

## 11. TDD Approach for Voice Agents

### 11.1 Test-First Development Workflow

**Recommended Approach (from AGENTS.md):**

> When modifying core agent behavior such as instructions, tool descriptions, and tasks/workflows/handoffs, never just guess what will work. Always use test-driven development (TDD) and begin by writing tests for the desired behavior.

**Workflow:**

1. **Write the test first** - Define expected behavior
2. **Run and watch it fail** - Understand what's missing
3. **Implement the feature** - Make the test pass
4. **Refactor** - Improve implementation while keeping test passing
5. **Run full suite** - Ensure no regressions

### 11.2 TDD Example: Adding a New Tool

```python
# Step 1: Write test for new tool

@pytest.mark.asyncio
async def test_calculator_tool():
    """Test new calculator tool."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        
        # Test that agent uses calculator tool correctly
        result = await session.run(user_input="What is 123 + 456?")
        
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Correctly calculates 123 + 456 = 579"
            )
        )


# Step 2: Run test - it fails (tool doesn't exist yet)
# $ uv run pytest tests/test_agent.py::test_calculator_tool
# FAILED - ToolError: Tool 'calculator' not found

# Step 3: Implement the tool

class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful assistant with calculator abilities."
        )
    
    @function_tool
    async def calculate(self, context: RunContext, expression: str) -> str:
        """Calculate a mathematical expression.
        
        Args:
            expression: The mathematical expression to evaluate (e.g., "2 + 2")
        """
        try:
            result = eval(expression)  # In production, use safe evaluator
            return f"The result is {result}"
        except Exception as e:
            raise ToolError(f"Invalid expression: {expression}")

# Step 4: Run test - it should pass now
# $ uv run pytest tests/test_agent.py::test_calculator_tool
# PASSED

# Step 5: Add more tests for edge cases
# Then run full suite to check for regressions
# $ uv run pytest tests/
```

### 11.3 TDD for Tool Changes

```python
# Test tool parameter validation first

@pytest.mark.asyncio
async def test_tool_validates_input():
    """Test that tool properly validates input."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        agent = Assistant()
        await session.start(agent)
        
        # Test that agent handles invalid input gracefully
        result = await session.run(user_input="Calculate 'abc def'")
        
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Clearly explains that the expression is invalid"
            )
        )


@pytest.mark.asyncio
async def test_tool_handles_division_by_zero():
    """Test division by zero handling."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        result = await session.run(user_input="Calculate 10 / 0")
        
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(
                llm,
                intent="Explains that division by zero is not possible"
            )
        )
```

### 11.4 Refactoring with Tests as Safety Net

```python
# Before refactoring: All tests pass

# Refactor the instructions
class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="""You are a helpful and friendly assistant.
            You can help with calculations and weather lookups.
            Always be polite and clear in your responses."""
            # Changed from previous version
        )

# Run tests to ensure refactoring didn't break behavior
# $ uv run pytest tests/test_agent.py -v
# All tests should still pass
```

---

## 12. Best Practices Summary

### Testing Best Practices

1. **Use async/await patterns** - All tests are async functions
2. **Context managers for resources** - Proper cleanup with `async with`
3. **Fixture scoping** - Use function-scoped fixtures for isolation
4. **Multiple assertions per test** - But keep tests focused
5. **Meaningful test names** - Describe what behavior is tested
6. **Judge for behavior** - Use `.judge()` for intent evaluation
7. **No more events check** - Always verify no unexpected output

### Tool Testing Best Practices

1. **Test in isolation** - Mock external dependencies
2. **Test error paths** - Invalid inputs, timeouts, API errors
3. **Verify LLM behavior** - Use judge to verify tool was called correctly
4. **Mock external APIs** - Don't make real API calls in tests
5. **Document expected behavior** - Clear docstrings and intent descriptions

### Development Best Practices

1. **Use TDD** - Write tests before implementation
2. **Run tests frequently** - After each change
3. **Full suite before commit** - `uv run pytest`
4. **Meaningful error messages** - Help diagnose failures
5. **Separate concerns** - One test per behavior

---

## 13. Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_agent.py

# Run specific test function
uv run pytest tests/test_agent.py::test_offers_assistance

# Run with verbose output
uv run pytest -v

# Run matching pattern
uv run pytest -k "test_offers"

# Run with output capture disabled (see print statements)
uv run pytest -s

# Run with detailed failure info
uv run pytest -vv

# Run specific test and show local variables on failure
uv run pytest -l tests/test_agent.py::test_offers_assistance
```

### CI/CD Integration

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: astral-sh/setup-uv@v2
      - run: uv sync
      - run: uv run pytest
```

---

## 14. References

- **LiveKit Docs:** https://docs.livekit.io/agents/
- **Testing Documentation:** https://docs.livekit.io/agents/build/testing/
- **Pytest Documentation:** https://docs.pytest.org/
- **Pytest-asyncio:** https://github.com/pytest-dev/pytest-asyncio
- **Example Tests:** `/my-app/tests/test_agent.py`

---

## Quick Reference Checklist

### Before Each Test
- [ ] Fixture properly initialized
- [ ] Context managers used (`async with`)
- [ ] LLM created fresh
- [ ] Session started before use

### Test Assertions
- [ ] Use `.expect.next_event()` for responses
- [ ] Use `.judge()` for LLM evaluation
- [ ] Use `.no_more_events()` to verify completeness
- [ ] Capture edge cases and errors

### Running Tests
- [ ] `uv run pytest` - Full suite before commit
- [ ] `uv run pytest -k pattern` - Quick testing
- [ ] `uv run pytest -vv` - Debug failures

### TDD Workflow
- [ ] Write test first
- [ ] Watch it fail
- [ ] Implement feature
- [ ] Watch it pass
- [ ] Run full suite
- [ ] Check for regressions


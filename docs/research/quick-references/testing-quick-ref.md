# LiveKit Agents Testing - Quick Reference

## One-Minute Setup

```python
import pytest
from livekit.agents import AgentSession, inference, llm
from agent import Assistant

def _llm() -> llm.LLM:
    return inference.LLM(model="openai/gpt-4.1-mini")

@pytest.mark.asyncio
async def test_my_agent() -> None:
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(Assistant())
        result = await session.run(user_input="Hello")
        await result.expect.next_event().is_message(role="assistant")
        result.expect.no_more_events()
```

## File Structure

```
my-app/
├── src/
│   └── agent.py          # Your agent
├── tests/
│   └── test_agent.py     # Tests here
├── pyproject.toml        # pytest config
└── .env.local            # API keys
```

## Run Tests

```bash
uv run pytest                           # All tests
uv run pytest -v                        # Verbose
uv run pytest -k test_name              # Single test
uv run pytest tests/test_agent.py -vv   # Detailed output
```

## Test Patterns

### Pattern 1: Basic Agent Test
```python
@pytest.mark.asyncio
async def test_greeting():
    async with (_llm() as llm, AgentSession(llm=llm) as session):
        await session.start(Assistant())
        result = await session.run(user_input="Hi")
        await result.expect.next_event().is_message(role="assistant")
        result.expect.no_more_events()
```

### Pattern 2: With LLM Judgment
```python
@pytest.mark.asyncio
async def test_friendliness():
    async with (_llm() as llm, AgentSession(llm=llm) as session):
        await session.start(Assistant())
        result = await session.run(user_input="Hello")
        await (
            result.expect.next_event()
            .is_message(role="assistant")
            .judge(llm, intent="Agent greets user warmly")
        )
        result.expect.no_more_events()
```

### Pattern 3: Multiple Turns
```python
@pytest.mark.asyncio
async def test_multi_turn():
    async with (_llm() as llm, AgentSession(llm=llm) as session):
        await session.start(Assistant())
        
        result1 = await session.run(user_input="Hi")
        await result1.expect.next_event().is_message(role="assistant")
        
        result2 = await session.run(user_input="What's your name?")
        await result2.expect.next_event().is_message(role="assistant")
```

### Pattern 4: Tool Testing
```python
@pytest.mark.asyncio
async def test_tool():
    from unittest.mock import patch, AsyncMock
    
    with patch('aiohttp.ClientSession.get') as mock:
        mock.return_value.__aenter__.return_value.json = AsyncMock(
            return_value={"result": "data"}
        )
        
        async with (_llm() as llm, AgentSession(llm=llm) as session):
            await session.start(Assistant())
            result = await session.run(user_input="Use the tool")
            await result.expect.next_event().is_message(role="assistant")
```

### Pattern 5: Direct Tool Test
```python
@pytest.mark.asyncio
async def test_tool_direct():
    from unittest.mock import Mock
    
    agent = Assistant()
    context = Mock()
    
    try:
        result = await agent.my_tool(context, "parameter")
        assert result == "expected"
    except ToolError as e:
        assert "error message" in str(e)
```

## Key Fixtures

```python
@pytest.fixture
async def llm_instance():
    async with inference.LLM(model="openai/gpt-4.1-mini") as llm:
        yield llm

@pytest.fixture
async def agent_session(llm_instance):
    async with AgentSession(llm=llm_instance) as session:
        yield session

@pytest.fixture
async def running_agent(agent_session):
    await agent_session.start(Assistant())
    yield agent_session
```

## Assertion API

```python
# Next event must be a message
await result.expect.next_event().is_message(role="assistant")

# Judge response with LLM
await result.expect.next_event().is_message(role="assistant").judge(
    llm,
    intent="Description of expected behavior"
)

# No more events after that
result.expect.no_more_events()
```

## pytest.ini Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
```

## Common Mistakes

1. **Forgetting async with** - Always use `async with` for context managers
2. **Not checking no_more_events()** - Always verify test completeness
3. **Real API calls in tests** - Mock external services with `@patch`
4. **No test for new behavior** - Write test before implementing feature
5. **Bad judge prompts** - Be specific about requirements and allow flexibility

## TDD Workflow

1. Write test → 2. Run (fails) → 3. Implement → 4. Run (passes) → 5. Refactor

## External Resources

- **Live Chat Testing:** https://docs.livekit.io/agents/build/testing/
- **Function Tools:** https://docs.livekit.io/agents/build/ai-functions/
- **Pytest Docs:** https://docs.pytest.org/
- **Pytest-asyncio:** https://github.com/pytest-dev/pytest-asyncio

## Judge Prompt Guidelines

Good prompt:
```
The agent should greet the user.

Must include:
- Friendly greeting
- No harmful content

May include:
- Offer to help
- Small talk
```

Bad prompt:
```
Agent should be nice
```

## Check Before Commit

- [ ] All tests pass: `uv run pytest`
- [ ] No new warnings
- [ ] Code formatted: `uv run ruff format`
- [ ] Tests for new features
- [ ] TDD followed for changes


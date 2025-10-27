# LiveKit Agents Function Tools - Quick Reference Guide

## Key Source Files

All LiveKit Agents implementation files are located in `.venv/lib/python3.12/site-packages/livekit/agents/`:

- **tool_context.py** - `@function_tool` decorator, `ToolError`, `StopResponse`
- **events.py** - `RunContext` class definition  
- **generation.py** - Tool execution pipeline, error handling, timeout management
- **llm/utils.py** - Parameter validation and schema generation
- **voice/agent.py** - `Agent` class with tool discovery
- **beta/workflows/email_address.py** - Real-world example implementation

## 1-Minute Summary

### Define a Tool
```python
from livekit.agents import Agent, function_tool, RunContext, ToolError

class MyAgent(Agent):
    def __init__(self):
        super().__init__(instructions="You are helpful.")
    
    @function_tool
    async def lookup_data(self, context: RunContext, query: str) -> str:
        """Look up information.
        
        Args:
            query: Search query
        """
        if not query:
            raise ToolError("Query cannot be empty")
        return f"Results for: {query}"
```

### Key Requirements
1. **Must use `async def`** - All tools are asynchronous
2. **RunContext parameter** - Access to session, speech control, user data
3. **Return primitives** - str, int, float, bool, None, dict, list (no complex objects)
4. **Raise ToolError** - For expected errors that LLM should handle
5. **Raise StopResponse** - When no follow-up response needed

## Common Patterns

### Error Handling
```python
@function_tool
async def process_payment(self, context: RunContext, amount: float) -> str:
    try:
        # Disable interruptions for critical operation
        context.disallow_interruptions()
        
        if amount <= 0:
            raise ToolError("Amount must be positive")
        
        result = await self._charge_card(amount)
        return f"Charged ${amount}"
    except asyncio.TimeoutError:
        raise ToolError("Payment service timed out")
    except Exception as e:
        raise ToolError("Payment failed")
```

### Timeout Management
```python
@function_tool
async def fetch_data(self, context: RunContext, url: str) -> str:
    try:
        data = await asyncio.wait_for(
            self._fetch_url(url),
            timeout=10.0
        )
        return data
    except asyncio.TimeoutError:
        raise ToolError("Request timed out after 10 seconds")
```

### Parameter Validation
```python
from typing import Annotated
from pydantic import Field

@function_tool
async def transfer_funds(
    self,
    context: RunContext,
    amount: Annotated[float, Field(gt=0, le=10000)],
    recipient: Annotated[str, Field(min_length=1, max_length=50)]
) -> str:
    """Transfer money.
    
    Args:
        amount: Amount in USD (0 < x <= 10000)
        recipient: Recipient ID
    """
    # Validation already done by Pydantic
    return f"Transferred ${amount} to {recipient}"
```

### RunContext Features
```python
@function_tool
async def confirm_action(self, context: RunContext) -> str:
    # Wait for agent's spoken response to finish before processing
    await context.wait_for_playout()
    
    # Prevent user interruption during critical operation
    context.disallow_interruptions()
    
    # Access session and user data
    user_id = context.userdata.get("user_id")
    session = context.session
    
    # Access function call info
    call_info = context.function_call
    
    return "Confirmed"
```

## Framework Features

### Automatic Tool Discovery
```python
class MyAgent(Agent):
    def __init__(self):
        super().__init__(instructions="...")
        # @function_tool decorated methods are automatically discovered
    
    @function_tool
    async def tool1(self, context: RunContext) -> str:
        return "tool1"
    
    @function_tool
    async def tool2(self, context: RunContext) -> str:
        return "tool2"
```

### Concurrent Execution
- LLM can call multiple tools in one turn
- Tools execute concurrently with asyncio
- One tool's timeout doesn't affect others
- All results collected before LLM responds

### Parameter Schema Generation
- **Docstrings** → Tool description
- **Type hints** → Parameter types
- **Pydantic Field** → Validation rules
- **Function signature** → LLM knows available parameters

### Error Processing
- `ToolError` → Message visible to LLM (can retry)
- `StopResponse` → No response needed
- Other exceptions → Generic "internal error" to LLM

## Common Mistakes to Avoid

1. **Using sync `def` instead of `async def`**
   ```python
   # WRONG
   @function_tool
   def my_tool(self, context: RunContext):
       return "result"
   
   # CORRECT
   @function_tool
   async def my_tool(self, context: RunContext):
       return "result"
   ```

2. **Returning complex objects**
   ```python
   # WRONG
   return SomeCustomClass()
   
   # CORRECT
   return {"name": "value", "count": 42}
   ```

3. **Not using ToolError for expected failures**
   ```python
   # WRONG
   if not found:
       return "Not found"  # LLM might think this is success
   
   # CORRECT
   if not found:
       raise ToolError("Item not found")
   ```

4. **Blocking operations**
   ```python
   # WRONG
   time.sleep(5)  # Blocks entire event loop
   
   # CORRECT
   await asyncio.sleep(5)
   ```

## Real-World Example: Email Collection Task

See `/livekit/agents/beta/workflows/email_address.py` for complete implementation showing:
- Complex workflow with multiple tools
- State management between tool calls
- Speech synchronization with `wait_for_playout()`
- Error propagation and validation
- Task completion pattern

## Testing

```python
import pytest
from livekit.agents import AgentSession, inference

@pytest.mark.asyncio
async def test_tool():
    async with AgentSession(llm=...) as session:
        await session.start(MyAgent())
        result = await session.run(user_input="trigger the tool")
        await result.expect.next_event().is_message(role="assistant")
```

## Documentation Links

- Official Docs: https://docs.livekit.io/agents/build/
- Function Tools: https://docs.livekit.io/agents/build/ai-functions/
- LiveKit SDK: https://github.com/livekit/agents

# LiveKit Agents Function Tools Implementation Research

## Executive Summary

LiveKit Agents provides a comprehensive function tools system for building voice AI agents with LLM integration. The implementation uses Python decorators, async/await patterns, Pydantic validation, and sophisticated error handling to enable tools to interact safely with external APIs and complex agent workflows.

---

## 1. Function Tool Decorator Implementation

### 1.1 Basic Decorator Pattern

**Location:** `/livekit/agents/llm/tool_context.py`

The `@function_tool` decorator is the primary mechanism for creating function tools. It supports two modes:

#### Standard Function Tool Mode
```python
@function_tool
async def lookup_weather(self, context: RunContext, location: str):
    """Use this tool to look up current weather information.
    
    Args:
        location: The location to look up weather information for (e.g. city name)
    """
    logger.info(f"Looking up weather for {location}")
    return "sunny with a temperature of 70 degrees."
```

#### Raw Function Tool Mode
```python
@function_tool(raw_schema={
    "name": "custom_tool",
    "description": "Custom tool with raw schema",
    "parameters": {"type": "object", "properties": {...}}
})
async def custom_tool(self, raw_arguments: dict[str, object]):
    # Handle raw JSON arguments directly
    pass
```

### 1.2 Decorator Implementation Details

```python
def function_tool(
    f: F | Raw_F | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
    raw_schema: RawFunctionDescription | dict[str, Any] | None = None,
) -> FunctionTool | RawFunctionTool | Callable[[F], FunctionTool] | Callable[[Raw_F], RawFunctionTool]:
    
    def deco_func(func: F) -> FunctionTool:
        from docstring_parser import parse_from_object
        
        docstring = parse_from_object(func)
        info = _FunctionToolInfo(
            name=name or func.__name__,
            description=description or docstring.description,
        )
        setattr(func, "__livekit_tool_info", info)
        return cast(FunctionTool, func)
    
    # Supports both immediate decoration and parameterized decoration
    if f is not None:
        return deco_raw(cast(Raw_F, f)) if raw_schema is not None else deco_func(cast(F, f))
    
    return deco_raw if raw_schema is not None else deco_func
```

**Key Features:**
- Automatically extracts tool name from function name
- Parses docstrings to populate tool description
- Supports parameterized naming and descriptions via decorator arguments
- Stores metadata using `__livekit_tool_info` attribute on the function

### 1.3 Tool Discovery

```python
def find_function_tools(cls_or_obj: Any) -> list[FunctionTool | RawFunctionTool]:
    methods: list[FunctionTool | RawFunctionTool] = []
    for _, member in inspect.getmembers(cls_or_obj):
        if is_function_tool(member) or is_raw_function_tool(member):
            methods.append(member)
    return methods
```

**Usage Pattern:**
```python
class Assistant(Agent):
    def __init__(self):
        super().__init__(
            instructions="...",
            # Tools are automatically discovered from decorated methods
        )
    
    @function_tool
    async def my_tool(self, context: RunContext, param: str):
        return "result"
```

Tools are discovered during Agent initialization:
```python
class Agent:
    def __init__(self, instructions: str, tools: list[FunctionTool | RawFunctionTool] | None = None):
        tools = tools or []
        self._tools = tools.copy() + find_function_tools(self)  # Auto-discovery
        self._chat_ctx = chat_ctx.copy(tools=self._tools)
```

---

## 2. RunContext Usage and Best Practices

### 2.1 RunContext Structure

**Location:** `/livekit/agents/voice/events.py`

```python
class RunContext(Generic[Userdata_T]):
    # private ctor
    def __init__(
        self,
        *,
        session: AgentSession[Userdata_T],
        speech_handle: SpeechHandle,
        function_call: FunctionCall,
    ) -> None:
        self._session = session
        self._speech_handle = speech_handle
        self._function_call = function_call
        self._initial_step_idx = speech_handle.num_steps - 1

    @property
    def session(self) -> AgentSession[Userdata_T]:
        """Access to the agent session context"""
        return self._session

    @property
    def speech_handle(self) -> SpeechHandle:
        """Handle for controlling speech generation"""
        return self._speech_handle

    @property
    def function_call(self) -> FunctionCall:
        """Information about the current function call"""
        return self._function_call

    @property
    def userdata(self) -> Userdata_T:
        """Access user-provided data from session"""
        return self.session.userdata
```

### 2.2 RunContext Key Methods

#### 2.2.1 Disable Interruptions
```python
def disallow_interruptions(self) -> None:
    """Disable interruptions for this FunctionCall.
    
    Raises:
        RuntimeError: If the SpeechHandle is already interrupted.
    """
    self.speech_handle.allow_interruptions = False
```

**Use Case:** Critical operations that must complete without user interruption
```python
@function_tool
async def process_payment(self, context: RunContext, amount: float):
    context.disallow_interruptions()  # Prevent user from interrupting payment
    # ... process payment
```

#### 2.2.2 Wait for Playout
```python
async def wait_for_playout(self) -> None:
    """Waits for the speech playout corresponding to this function call step.
    
    Unlike `SpeechHandle.wait_for_playout`, which waits for the full
    assistant turn to complete (including all function tools),
    this method only waits for the assistant's spoken response prior running
    this tool to finish playing.
    """
    await self.speech_handle._wait_for_generation(step_idx=self._initial_step_idx)
```

**Real-World Example from LiveKit:**
```python
@function_tool
async def confirm_email_address(self, ctx: RunContext) -> None:
    """Validates/confirms the email address provided by the user."""
    await ctx.wait_for_playout()  # Wait for agent to finish speaking
    
    # Now check if user actually confirmed (wasn't just in previous turn)
    if ctx.speech_handle == self._email_update_speech_handle:
        raise ToolError("error: the user must confirm the email address explicitly")
    
    if not self._current_email.strip():
        raise ToolError("no email address were provided")
    
    if not self.done():
        self.complete(GetEmailResult(email_address=self._current_email))
```

### 2.3 Best Practices for RunContext

1. **Always inject RunContext when needed:**
   ```python
   async def my_tool(self, context: RunContext, param: str):
       # RunContext will be automatically injected by the framework
       pass
   ```

2. **Access session data safely:**
   ```python
   async def fetch_user_data(self, context: RunContext):
       # Access user context
       user_id = context.userdata.get("user_id")
       session = context.session
   ```

3. **Control interruptions for sensitive operations:**
   ```python
   async def process_payment(self, context: RunContext, amount: float):
       context.disallow_interruptions()
       # Critical section - cannot be interrupted
   ```

4. **Synchronize with speech output:**
   ```python
   async def require_confirmation(self, context: RunContext):
       await context.wait_for_playout()
       # Now safe to process user confirmation
   ```

---

## 3. Async Function Patterns

### 3.1 Async/Await Requirement

All function tools MUST be async:
```python
@function_tool
async def my_tool(self, context: RunContext, param: str):  # Must use 'async'
    result = await some_async_operation()
    return result
```

**Invalid Pattern (will not work):**
```python
@function_tool
def my_tool(self, param: str):  # Missing 'async' - ERROR!
    return "result"
```

### 3.2 Concurrent Execution Pattern

**Location:** `/livekit/agents/voice/generation.py` (line 367-581)

The framework executes multiple function calls concurrently:
```python
tasks: list[asyncio.Task[Any]] = []
try:
    async for fnc_call in function_stream:
        # Create async task for each function call
        task = asyncio.create_task(_traceable_fnc_tool(function_callable, fnc_call))
        _set_activity_task_info(task, speech_handle=speech_handle, function_call=fnc_call)
        tasks.append(task)
        task.add_done_callback(lambda task: tasks.remove(task))
    
    # Wait for all tasks to complete
    await asyncio.shield(asyncio.gather(*tasks, return_exceptions=True))
finally:
    await utils.aio.cancel_and_wait(*tasks)
```

**Best Practices:**
1. Use `asyncio` for I/O-bound operations
2. Avoid blocking operations (use async libraries instead)
3. Handle cancellation gracefully

### 3.3 External API Integration Pattern

```python
import aiohttp
import asyncio

class WeatherAgent(Agent):
    @function_tool
    async def get_weather(self, context: RunContext, city: str):
        """Get current weather for a city.
        
        Args:
            city: City name to fetch weather for
        """
        try:
            # Use async HTTP client
            async with aiohttp.ClientSession() as session:
                url = f"https://api.weather.example.com/current?city={city}"
                async with session.get(url) as resp:
                    if resp.status != 200:
                        raise ToolError(f"Weather service returned {resp.status}")
                    data = await resp.json()
                    return f"Current weather: {data['condition']}"
        except asyncio.TimeoutError:
            raise ToolError("Weather service request timed out")
        except Exception as e:
            raise ToolError(f"Failed to fetch weather: {str(e)}")
```

### 3.4 Timeout Handling

While not explicitly configured per-tool, timeouts are managed at the session level. For long-running operations, implement your own timeout:

```python
@function_tool
async def long_operation(self, context: RunContext):
    """Long-running operation with timeout."""
    try:
        # Implement 30-second timeout
        result = await asyncio.wait_for(
            self._expensive_operation(),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        raise ToolError("Operation timed out after 30 seconds")
```

---

## 4. Tool Parameter Definitions and Validation

### 4.1 Automatic Schema Generation from Function Signature

**Location:** `/livekit/agents/llm/utils.py` (line 302-345)

```python
def function_arguments_to_pydantic_model(func: Callable[..., Any]) -> type[BaseModel]:
    """Create a Pydantic model from a function's signature."""
    
    from docstring_parser import parse_from_object
    
    docstring = parse_from_object(func)
    param_docs = {p.arg_name: p.description for p in docstring.params}
    
    signature = inspect.signature(func)
    type_hints = get_type_hints(func, include_extras=True)
    
    fields: dict[str, Any] = {}
    
    for param_name, param in signature.parameters.items():
        type_hint = type_hints[param_name]
        
        # Skip RunContext parameters
        if is_context_type(type_hint):
            continue
        
        # Extract default values
        default_value = param.default if param.default is not param.empty else ...
        field_info = Field()
        
        # Handle Annotated types with Field metadata
        if get_origin(type_hint) is Annotated:
            annotated_args = get_args(type_hint)
            type_hint = annotated_args[0]
            field_info = next(
                (x for x in annotated_args[1:] if isinstance(x, FieldInfo)), 
                field_info
            )
        
        # Apply defaults and descriptions
        if default_value is not ... and field_info.default is PydanticUndefined:
            field_info.default = default_value
        
        if field_info.description is None:
            field_info.description = param_docs.get(param_name, None)
        
        fields[param_name] = (type_hint, field_info)
    
    return create_model(f"{func.__name__.capitalize()}Args", **fields)
```

### 4.2 Parameter Definition Patterns

#### 4.2.1 Simple Parameters
```python
from typing import Annotated
from pydantic import Field

@function_tool
async def search_documents(
    self,
    context: RunContext,
    query: str,  # Required string parameter
    max_results: int = 10  # Optional with default
):
    """Search for documents.
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return
    """
    pass
```

#### 4.2.2 Annotated Parameters with Metadata
```python
@function_tool
async def process_order(
    self,
    context: RunContext,
    amount: Annotated[float, Field(
        description="Order amount in USD",
        gt=0,  # Greater than 0
        le=10000  # Less than or equal to 10000
    )],
    currency: str = "USD"
):
    """Process an order payment.
    
    Args:
        amount: Order amount (must be positive, max $10,000)
        currency: Currency code (default USD)
    """
    if amount <= 0:
        raise ToolError("Amount must be positive")
    pass
```

#### 4.2.3 Complex Types
```python
from typing import Optional, List
from pydantic import BaseModel

class ContactInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

@function_tool
async def create_contact(
    self,
    context: RunContext,
    contact: ContactInfo
):
    """Create a new contact.
    
    Args:
        contact: Contact information object
    """
    pass
```

### 4.3 Validation and Error Handling

```python
from pydantic import ValidationError
from livekit.agents import ToolError

@function_tool
async def transfer_funds(
    self,
    context: RunContext,
    amount: Annotated[float, Field(gt=0)],
    recipient: Annotated[str, Field(min_length=1)]
):
    """Transfer funds to a recipient.
    
    Args:
        amount: Amount to transfer (must be positive)
        recipient: Recipient identifier
    """
    # Parameter validation happens automatically via Pydantic
    # If validation fails, a ValidationError is caught by the framework
    # and converted to a ToolError for the LLM
    
    if amount > 10000:
        raise ToolError("Single transfer limited to $10,000")
    
    if len(recipient) > 50:
        raise ToolError("Recipient identifier too long")
    
    return f"Transferred ${amount} to {recipient}"
```

**Validation happens at two levels:**

1. **Pydantic-level (framework):** Type checking, range validation
2. **Function-level:** Business logic validation

---

## 5. Error Handling in Tools

### 5.1 Error Handling Classes

**Location:** `/livekit/agents/llm/tool_context.py` (lines 48-76)

#### 5.1.1 ToolError - Expected Errors
```python
class ToolError(Exception):
    def __init__(self, message: str) -> None:
        """
        Exception raised within AI functions for expected errors.
        
        The provided message will be visible to the LLM, allowing it to
        understand the context of the error.
        """
        super().__init__(message)
        self._message = message
    
    @property
    def message(self) -> str:
        return self._message
```

**Usage:**
```python
@function_tool
async def update_email_address(self, context: RunContext, email: str) -> str:
    """Update the email address provided by the user."""
    email = email.strip()
    
    if not re.match(EMAIL_REGEX, email):
        # LLM will see this message and can try again
        raise ToolError(f"Invalid email address provided: {email}")
    
    return f"Email updated to {email}"
```

#### 5.1.2 StopResponse - No Response Needed
```python
class StopResponse(Exception):
    def __init__(self) -> None:
        """
        Exception raised to indicate the agent should not generate a response
        for the current function call.
        """
        super().__init__()
```

**Usage:**
```python
@function_tool
async def stop_conversation(self, context: RunContext):
    """End the conversation without further response."""
    # Agent won't generate a follow-up response
    raise StopResponse()
```

### 5.2 Error Processing Pipeline

**Location:** `/livekit/agents/voice/generation.py` (lines 620-665)

```python
def make_tool_output(
    *, fnc_call: llm.FunctionCall, output: Any, exception: BaseException | None
) -> ToolExecutionOutput:
    """Process tool execution result and exceptions."""
    
    # Support returning Exception instead of raising
    if isinstance(output, BaseException):
        exception = output
        output = None
    
    # Handle ToolError - message sent to LLM
    if isinstance(exception, ToolError):
        return ToolExecutionOutput(
            fnc_call=fnc_call.model_copy(),
            fnc_call_out=llm.FunctionCallOutput(
                name=fnc_call.name,
                call_id=fnc_call.call_id,
                output=exception.message,  # LLM sees this
                is_error=True,
            ),
            agent_task=None,
            raw_output=output,
            raw_exception=exception,
        )
    
    # Handle StopResponse - no output sent
    if isinstance(exception, StopResponse):
        return ToolExecutionOutput(
            fnc_call=fnc_call.model_copy(),
            fnc_call_out=None,  # No output
            agent_task=None,
            raw_output=output,
            raw_exception=exception,
        )
    
    # Handle unexpected exceptions - generic message sent to LLM
    if exception is not None:
        return ToolExecutionOutput(
            fnc_call=fnc_call.model_copy(),
            fnc_call_out=llm.FunctionCallOutput(
                name=fnc_call.name,
                call_id=fnc_call.call_id,
                output="An internal error occurred",  # Don't expose internals!
                is_error=True,
            ),
            agent_task=None,
            raw_output=output,
            raw_exception=exception,
        )
```

### 5.3 Comprehensive Error Handling Example

```python
import aiohttp
from livekit.agents import ToolError, StopResponse, RunContext, function_tool
from pydantic import Field
from typing import Annotated
import asyncio

class EmailTask(AgentTask[GetEmailResult]):
    @function_tool
    async def update_email_address(
        self,
        context: RunContext,
        email: Annotated[str, Field(min_length=5)]
    ) -> str:
        """Update the email address.
        
        Args:
            email: The email address to validate and store
        """
        # 1. Parameter validation (Pydantic handles min_length)
        email = email.strip()
        
        # 2. Business logic validation
        if not self._is_valid_email(email):
            raise ToolError(f"Invalid email format: {email}")
        
        # 3. Duplicate checking with error handling
        try:
            if await self._is_duplicate_email(email):
                raise ToolError("This email is already registered")
        except asyncio.TimeoutError:
            raise ToolError("Email verification service unavailable")
        except Exception as e:
            # Log internal errors, but don't expose them to LLM
            logger.exception(f"Unexpected error checking email: {e}")
            raise ToolError("Could not verify email at this time")
        
        self._current_email = email
        return f"Email confirmed: {email}"
    
    @function_tool
    async def confirm_email_address(self, context: RunContext) -> None:
        """Confirm the provided email."""
        # Wait for speech to finish before confirming
        await context.wait_for_playout()
        
        # Validate state
        if not self._current_email:
            raise ToolError("No email address to confirm")
        
        # Check for duplicate confirmations in same turn
        if context.speech_handle == self._email_update_speech_handle:
            raise ToolError("User must provide explicit confirmation")
        
        # Success - complete the task
        self.complete(GetEmailResult(email_address=self._current_email))
    
    @function_tool
    async def decline_email_capture(self, context: RunContext, reason: str) -> None:
        """Handle user declining to provide email."""
        # Return error as result (for task completion)
        if not self.done():
            self.complete(ToolError(f"Email capture declined: {reason}"))
```

---

## 6. Tool Response Formatting

### 6.1 Valid Response Types

**Location:** `/livekit/agents/voice/generation.py` (lines 590-607)

```python
def _is_valid_function_output(value: Any) -> bool:
    VALID_TYPES = (str, int, float, bool, complex, type(None))
    
    # Primitive types
    if isinstance(value, VALID_TYPES):
        return True
    
    # Collections of valid types
    elif isinstance(value, (list, set, frozenset, tuple)):
        return all(_is_valid_function_output(item) for item in value)
    
    # Dictionaries with valid types
    elif isinstance(value, dict):
        return all(
            isinstance(key, VALID_TYPES) and _is_valid_function_output(val)
            for key, val in value.items()
        )
    
    return False
```

**Supported Return Types:**
- `str` - Most common
- `int`, `float`, `bool`, `complex` - Numeric responses
- `None` - No output needed
- `list`, `dict`, `tuple`, `set` - Collections of valid types
- `Agent`, `AgentTask` - Handoff to another agent

### 6.2 Response Patterns

#### 6.2.1 String Responses
```python
@function_tool
async def get_user_info(self, context: RunContext, user_id: str) -> str:
    """Get information about a user."""
    user = await self._fetch_user(user_id)
    return f"User: {user.name}, Email: {user.email}"
```

#### 6.2.2 Dictionary Responses
```python
@function_tool
async def get_weather(self, context: RunContext, city: str) -> dict:
    """Get weather information."""
    data = await self._fetch_weather(city)
    return {
        "temperature": data.temp,
        "condition": data.condition,
        "humidity": data.humidity
    }
```

#### 6.2.3 Multiple Outputs with Lists
```python
@function_tool
async def search_products(self, context: RunContext, query: str) -> list:
    """Search for products."""
    results = await self._search(query)
    return [
        {
            "id": r.id,
            "name": r.name,
            "price": r.price
        }
        for r in results
    ]
```

#### 6.2.4 Agent Handoff
```python
@function_tool
async def transfer_to_billing(self, context: RunContext) -> Agent:
    """Transfer to billing department."""
    # Return an agent to hand off to
    return BillingAgent()
```

#### 6.2.5 Task Handoff
```python
@function_tool
async def collect_email(self, context: RunContext) -> AgentTask:
    """Collect email from user."""
    email_task = GetEmailTask()
    result = await email_task  # Await the task
    return f"Collected email: {result.email_address}"
```

### 6.3 Response Formatting Best Practices

1. **Keep responses concise:**
   ```python
   # Good
   return "Order confirmed: $99.99"
   
   # Avoid
   return "Order confirmed: $99.99. Thank you for shopping..."  # Duplicates TTS
   ```

2. **Use structured data when helpful:**
   ```python
   return {
       "status": "success",
       "confirmation_id": "12345",
       "total": "$99.99"
   }
   ```

3. **Format for LLM clarity:**
   ```python
   return """
   Flight found:
   - Airline: United Airlines
   - Departure: 2:30 PM
   - Price: $299
   """
   ```

---

## 7. Managing Tool Execution Timeouts

### 7.1 Framework-Level Timeout Management

The LiveKit Agents framework manages timeouts at the session/activity level, but individual tools should implement their own timeout handling for robust behavior.

### 7.2 Per-Tool Timeout Implementation

#### 7.2.1 Simple Timeout Pattern
```python
import asyncio

@function_tool
async def fetch_data(self, context: RunContext, url: str) -> str:
    """Fetch data from URL with timeout."""
    try:
        # 10-second timeout
        async with aiohttp.ClientSession() as session:
            async with asyncio.timeout(10):  # Python 3.11+
                async with session.get(url) as resp:
                    return await resp.text()
    except asyncio.TimeoutError:
        raise ToolError("Data fetch timed out after 10 seconds")
```

#### 7.2.2 Backward Compatible Timeout
```python
@function_tool
async def process_request(self, context: RunContext, data: str) -> str:
    """Process request with timeout."""
    try:
        result = await asyncio.wait_for(
            self._process_async(data),
            timeout=5.0  # 5-second timeout
        )
        return result
    except asyncio.TimeoutError:
        raise ToolError("Processing timed out after 5 seconds")
    except Exception as e:
        logger.exception(f"Processing error: {e}")
        raise ToolError(f"Processing failed: {str(e)}")
```

### 7.3 Concurrent Tool Timeout Handling

The framework uses `asyncio.gather()` with `return_exceptions=True` for concurrent tool execution:

```python
# From generation.py line 567
await asyncio.shield(asyncio.gather(*tasks, return_exceptions=True))
```

This ensures:
- One tool's timeout doesn't affect others
- All tools execute concurrently
- Exceptions are collected but don't break the loop

### 7.4 Graceful Degradation Pattern

```python
@function_tool
async def get_user_recommendations(
    self,
    context: RunContext,
    user_id: str
) -> str:
    """Get recommendations with graceful fallback."""
    try:
        # Try primary recommendation engine with timeout
        result = await asyncio.wait_for(
            self._ml_engine.get_recommendations(user_id),
            timeout=3.0
        )
        return f"Recommended: {result}"
    except asyncio.TimeoutError:
        logger.warning(f"ML engine timeout for user {user_id}")
        # Fallback to simple recommendations
        try:
            fallback = await asyncio.wait_for(
                self._simple_recommendations(user_id),
                timeout=1.0
            )
            return f"Popular items: {fallback}"
        except asyncio.TimeoutError:
            raise ToolError("Unable to fetch recommendations")
```

### 7.5 Resource Cleanup on Timeout

```python
@function_tool
async def long_operation(self, context: RunContext):
    """Long operation with proper cleanup."""
    connection = None
    try:
        connection = await asyncio.wait_for(
            self._create_connection(),
            timeout=5.0
        )
        
        result = await asyncio.wait_for(
            self._perform_operation(connection),
            timeout=30.0
        )
        return result
    except asyncio.TimeoutError:
        raise ToolError("Operation timed out")
    finally:
        # Ensure cleanup happens even on timeout
        if connection:
            await connection.close()
```

---

## 8. Complex Tool Integration Examples

### 8.1 Email Validation Task (Real LiveKit Example)

**Location:** `/livekit/agents/beta/workflows/email_address.py`

```python
class GetEmailTask(AgentTask[GetEmailResult]):
    """Complex workflow for collecting and validating email addresses."""
    
    def __init__(self, ...):
        super().__init__(
            instructions=(
                "Handle input as noisy voice transcription. Expect emails like:\n"
                "- 'john dot doe at gmail dot com'\n"
                "- 'susan underscore smith at yahoo dot co dot uk'\n"
                "Normalize patterns silently and validate via tools."
            ),
            ...
        )
        self._current_email = ""
        self._email_update_speech_handle: SpeechHandle | None = None
    
    async def on_enter(self) -> None:
        """Initialization when task starts."""
        self.session.generate_reply(
            instructions="Ask the user to provide an email address."
        )
    
    @function_tool
    async def update_email_address(self, email: str, ctx: RunContext) -> str:
        """Update email with validation."""
        self._email_update_speech_handle = ctx.speech_handle
        email = email.strip()
        
        # Regex validation
        if not re.match(EMAIL_REGEX, email):
            raise ToolError(f"Invalid email address: {email}")
        
        self._current_email = email
        separated_email = " ".join(email)
        
        return (
            f"Email updated to {email}\n"
            f"Character by character: {separated_email}\n"
            f"Please confirm"
        )
    
    @function_tool
    async def confirm_email_address(self, ctx: RunContext) -> None:
        """Confirm the email."""
        await ctx.wait_for_playout()
        
        if ctx.speech_handle == self._email_update_speech_handle:
            raise ToolError("User must provide explicit confirmation")
        
        if not self._current_email.strip():
            raise ToolError("No email address provided")
        
        if not self.done():
            self.complete(GetEmailResult(email_address=self._current_email))
    
    @function_tool
    async def decline_email_capture(self, reason: str) -> None:
        """Handle decline."""
        if not self.done():
            self.complete(ToolError(f"Email capture declined: {reason}"))
```

### 8.2 External API Integration Pattern

```python
class WeatherAgent(Agent):
    def __init__(self):
        super().__init__(
            instructions="You are a helpful weather assistant."
        )
        self._api_key = os.getenv("WEATHER_API_KEY")
    
    @function_tool
    async def get_current_weather(
        self,
        context: RunContext,
        location: Annotated[str, Field(
            description="City name or coordinates",
            min_length=1
        )]
    ) -> str:
        """Get current weather for a location.
        
        Args:
            location: City name or lat,lon coordinates
        """
        if not self._api_key:
            raise ToolError("Weather service not configured")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Timeout for the entire request
                result = await asyncio.wait_for(
                    self._fetch_weather_data(session, location),
                    timeout=5.0
                )
                
                # Format response for LLM
                return self._format_weather_response(result)
        
        except asyncio.TimeoutError:
            raise ToolError("Weather service timed out")
        except aiohttp.ClientError as e:
            logger.error(f"Weather API error: {e}")
            raise ToolError("Unable to fetch weather data")
    
    async def _fetch_weather_data(self, session, location):
        """Fetch data from weather API."""
        url = f"https://api.weather.service/current"
        params = {
            "location": location,
            "apikey": self._api_key
        }
        
        async with session.get(url, params=params) as resp:
            if resp.status == 404:
                raise ToolError(f"Location not found: {location}")
            elif resp.status != 200:
                raise ToolError(f"Weather service error (status {resp.status})")
            
            return await resp.json()
    
    def _format_weather_response(self, data):
        """Format weather data for LLM."""
        return (
            f"Current weather in {data['location']}:\n"
            f"Temperature: {data['temperature']}°F\n"
            f"Conditions: {data['description']}\n"
            f"Humidity: {data['humidity']}%"
        )
```

### 8.3 Database Query with Connection Pooling

```python
class DatabaseAgent(Agent):
    def __init__(self, db_pool):
        super().__init__(instructions="Database assistant")
        self.db_pool = db_pool
    
    @function_tool
    async def query_user_profile(
        self,
        context: RunContext,
        user_id: Annotated[int, Field(gt=0)]
    ) -> str:
        """Query user profile from database."""
        conn = None
        try:
            # Get connection from pool with timeout
            conn = await asyncio.wait_for(
                self.db_pool.acquire(),
                timeout=2.0
            )
            
            # Execute query with timeout
            result = await asyncio.wait_for(
                conn.fetchrow(
                    "SELECT id, name, email FROM users WHERE id = $1",
                    user_id
                ),
                timeout=3.0
            )
            
            if not result:
                raise ToolError(f"User {user_id} not found")
            
            return f"User: {result['name']}, Email: {result['email']}"
        
        except asyncio.TimeoutError:
            raise ToolError("Database query timed out")
        except Exception as e:
            logger.exception(f"Database error: {e}")
            raise ToolError("Unable to query user profile")
        finally:
            # Always return connection to pool
            if conn:
                await self.db_pool.release(conn)
```

---

## 9. Testing Function Tools

**Location:** `/tests/test_agent.py`

```python
@pytest.mark.asyncio
async def test_weather_tool():
    """Test tool integration."""
    async with (
        _llm() as llm,
        AgentSession(llm=llm) as session,
    ):
        await session.start(WeatherAgent())
        
        # Run agent turn with input that triggers the tool
        result = await session.run(user_input="What's the weather in New York?")
        
        # Verify response contains weather data
        await result.expect.next_event().is_message(role="assistant")
        result.expect.no_more_events()
```

---

## Key Takeaways

1. **Function tools use Python decorators** with automatic parameter discovery
2. **RunContext provides session access** with interruption control and playout synchronization
3. **All tools must be async** using async/await patterns
4. **Parameter validation** happens via Pydantic with docstring parsing
5. **Error handling** uses `ToolError` (visible to LLM) vs exceptions (hidden)
6. **Response formatting** supports primitives, collections, and agent handoffs
7. **Timeout handling** should be implemented per-tool with graceful fallbacks
8. **Concurrent execution** means tools run in parallel with proper resource cleanup


# Agent Email Context Implementation

## The Elegant Solution

Make the email available to the agent as a pre-known fact, like knowing someone's name when they've already introduced themselves.

---

## Implementation Changes

### 1. Store Email in Agent Instance (agent.py ~line 240)

```python
class PandaDocAgent(Agent):
    def __init__(self):
        # ... existing initialization ...

        # Add this to store user context
        self.user_email = None  # Will be populated from metadata
        self.user_name = None   # Optional: if you collect name too

        # ... rest of initialization ...
```

### 2. Update Agent Instructions to Reference Known Email (agent.py ~line 150)

Add this to your agent instructions:

```python
### IMPORTANT CONTEXT
You already have the user's email address from their registration form.
- Their email is: {user_email}
- When booking meetings or referencing their email, use this known email
- Confirm it naturally: "I'll send the invite to [email] that you provided"
- Never ask for their email again unless they want to change it
```

Then modify the instruction initialization (line ~195):

```python
def __init__(self):
    # After setting self.user_email = None

    # Build dynamic instructions with email context
    base_instructions = """[your existing instructions]"""

    # This will be updated when we get the email from metadata
    self.dynamic_instructions = base_instructions

    super().__init__(instructions=self.dynamic_instructions)
```

### 3. Update Email Extraction to Set Context (agent.py ~line 950)

```python
async def entrypoint(ctx: JobContext):
    # ... existing code ...

    # Create agent instance
    agent = PandaDocAgent()

    # Extract user metadata from participant
    try:
        participants = ctx.room.remote_participants
        if participants:
            participant = list(participants.values())[0]
            if participant.metadata:
                metadata = json.loads(participant.metadata)

                # Store email in agent instance AND session data
                user_email = metadata.get('user_email', '')
                agent.user_email = user_email
                agent.session_data['user_email'] = user_email

                # Update agent instructions with actual email
                if user_email:
                    agent.instructions = agent.instructions.replace(
                        '{user_email}',
                        user_email
                    )
                    logger.info(f"Agent context set with email: {user_email}")
    except Exception as e:
        logger.warning(f"Could not extract participant metadata: {e}")
```

### 4. Modify book_sales_meeting to Use Known Email (agent.py ~line 677)

```python
@agent_function(
    description=(
        "Books a sales meeting with PandaDoc team for qualified trial users. "
        "Automatically uses the email address provided during registration."
    )
)
async def book_sales_meeting(
    context: RunContext,
    customer_name: str,
    customer_email: Optional[str] = None,  # Make email optional
    preferred_date: Optional[str] = None,
    preferred_time: Optional[str] = None,
):
    """
    Book a sales consultation meeting for qualified PandaDoc trial users.

    The email will be automatically filled from registration data if not provided.
    """
    # Use provided email or fall back to stored email
    email_to_use = customer_email or self.user_email

    if not email_to_use:
        raise ToolError(
            "I don't have your email address on file. "
            "Could you please provide it so I can send you the meeting invite?"
        )

    # Confirm the email naturally
    await context.send_message(
        f"Perfect! I'll send the meeting invite to {email_to_use} "
        f"(the email you provided when you started this call)."
    )

    # ... rest of the booking logic using email_to_use ...
```

### 5. Natural Conversation Patterns

Update your agent to reference the email naturally in conversation:

```python
# In agent instructions or responses:

GOOD: "I'll send that to the email you provided earlier"
GOOD: "I have your email from registration, so I'll send the invite there"
GOOD: "Let me book that meeting for you - I'll send it to [email]"

BAD: "What's your email address?" (when we already have it)
BAD: No mention of email at all (seems impersonal)
```

---

## Complete Minimal Implementation

Here's the absolute simplest version that just works:

### Option A: Super Simple (Recommended)

```python
class PandaDocAgent(Agent):
    def __init__(self, user_email=None):
        self.user_email = user_email

        # Include email context in instructions if available
        email_context = (
            f"\n\nIMPORTANT: The user's email is {user_email}. "
            f"Use this for booking meetings. Don't ask for it again."
            if user_email else ""
        )

        super().__init__(
            instructions=existing_instructions + email_context
        )

# In entrypoint function:
async def entrypoint(ctx: JobContext):
    # Extract email from metadata
    user_email = None
    try:
        if ctx.room.remote_participants:
            participant = list(ctx.room.remote_participants.values())[0]
            if participant.metadata:
                metadata = json.loads(participant.metadata)
                user_email = metadata.get('user_email')
    except:
        pass

    # Create agent with email context
    agent = PandaDocAgent(user_email=user_email)

    # ... rest of setup ...
```

### Option B: Even Simpler (Global Variable)

```python
# At module level
USER_EMAIL = None

# In entrypoint, after extracting metadata:
global USER_EMAIL
USER_EMAIL = metadata.get('user_email')

# In book_sales_meeting tool:
email_to_use = customer_email or USER_EMAIL
```

---

## Why This is Elegant

1. **Single Source of Truth**: Email comes from form, flows through naturally
2. **No Repetition**: User provides email once, agent remembers it
3. **Natural Conversation**: Agent references "the email you provided"
4. **Graceful Fallback**: If email is missing, agent can still ask for it
5. **No Over-Engineering**: Just passing a variable through the system

---

## Testing the Flow

1. **User fills form** with email: `john@company.com`
2. **Agent starts** and says: "Hi! I see you're from company.com..."
3. **User asks** to book a meeting
4. **Agent responds**: "I'll send the invite to john@company.com"
5. **No email prompt** needed!

---

## Advanced: Making It Conversational

If you want the agent to be even more natural:

```python
# In agent instructions
"""
When you first greet the user, you can reference their email domain naturally:
- If email is from a company domain: "I see you're from [Company]!"
- If email is gmail/personal: Don't mention it
- When booking: "I'll send this to your [company] email"

Examples:
- john@acme.com → "Hi! I see you're from Acme!"
- sarah@gmail.com → "Hi Sarah!" (don't mention gmail)
"""

# Extract domain for context
if self.user_email:
    domain = self.user_email.split('@')[1]
    if domain not in ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com']:
        company_name = domain.split('.')[0].title()
        # Add to context
```

---

## Final Recommendation

**Go with Option A (Simple class initialization)** because:
- Clean, clear code structure
- Email is properly scoped to the agent instance
- Easy to test and debug
- Natural upgrade path if you add more context later

This way the agent never has to ask for email when booking meetings - it just knows it, like a helpful assistant who remembers what you told them earlier.
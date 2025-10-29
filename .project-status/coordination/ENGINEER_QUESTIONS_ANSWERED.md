# Frontend Engineer Questions - Answered

**Date**: 2025-10-29
**Status**: Ready for Implementation

---

## Question 1: Metadata Field Name

**Q**: What should we call the email field in participant metadata?
- `user_email`?
- `business_email`?
- `trialist_email`?

### ✅ Answer: Use `user_email`

**Rationale**:
- **Standard convention**: Most systems use `user_email` as the canonical field name
- **Consistency**: Your frontend already stores it as `formData.email`
- **Future-proof**: If you add more user fields (name, phone), they follow the pattern: `user_name`, `user_phone`
- **Agent clarity**: Clear that this is the user's email, not system email or support email

**Implementation**:
```typescript
// Backend: route.ts
const metadata = {
  user_email: body.user_email,  // ✅ Use this name
  session_start: new Date().toISOString(),
};
```

```python
# Agent: agent.py
user_email = metadata.get('user_email')  # ✅ Matches backend
```

**Additional Context Field**:
If you want to preserve that it's from the form, you can add:
```typescript
const metadata = {
  user_email: body.user_email,
  email_source: 'registration_form',  // Optional context
  session_start: new Date().toISOString(),
};
```

---

## Question 2: Backend Type Safety & Validation

**Q**: Should I add email validation to route.ts?

### ✅ Answer: Yes, add basic validation

Add these checks in `route.ts`:

```typescript
export async function POST(request: Request) {
  try {
    // Environment variable checks...

    // Parse request body
    const body = await request.json();

    // ✅ VALIDATION: Email format check
    const userEmail = body.user_email || '';

    // Basic email validation (optional but recommended)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (userEmail && !emailRegex.test(userEmail)) {
      console.warn('Invalid email format provided:', userEmail);
      // Don't fail - just log warning and proceed with empty email
      // This maintains graceful degradation
    }

    // Generate room and participant info...
    const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;
    const participantIdentity = `trialist_${Date.now()}`;
    const participantName = 'PandaDoc Trialist';

    // Create metadata object
    const metadata = {
      user_email: userEmail,  // Will be empty string if invalid
      session_start: new Date().toISOString(),
    };

    // Create token with metadata
    const participantToken = await createParticipantToken(
      {
        identity: participantIdentity,
        name: participantName,
        metadata: JSON.stringify(metadata)
      },
      roomName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };

    return NextResponse.json(data, {
      headers: new Headers({ 'Cache-Control': 'no-store' })
    });

  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}
```

**Validation Strategy**: **Warn but don't fail**

**Rationale**:
- **Graceful degradation**: If email is invalid, session still works
- **Agent handles it**: Agent can ask for email if needed
- **User experience**: Don't block user from getting help
- **Logging**: You'll know if there's a problem via logs

**Don't return 400** because:
1. Email is optional context, not required for connection
2. You want the call to succeed even with bad data
3. Agent can recover by asking user for email

**Alternative (Stricter)**:
If you want to enforce email before allowing call:
```typescript
if (!userEmail || !emailRegex.test(userEmail)) {
  return new NextResponse(
    'Valid email required for trial assistance',
    { status: 400 }
  );
}
```

**My recommendation**: Use the warn-but-don't-fail approach above.

---

## Question 3: SessionStorage Format

**Q**: Should we keep JSON object or change to direct string?

### ✅ Answer: Keep as JSON object `{email: "..."}`

**Rationale**:
- **Future extensibility**: You might add name, company, phone later
- **Already working**: Frontend already uses this format
- **Type safety**: Easier to validate structure
- **Clear semantics**: `formData.email` vs. just a string

**Current Implementation (Keep This)**:
```typescript
// WelcomeView.tsx - Form submission
const handleStartCall = () => {
  sessionStorage.setItem('userFormData', JSON.stringify(formData));
  onStartCall();
};

// useRoom.ts - Retrieval
const storedData = sessionStorage.getItem('userFormData');
if (storedData) {
  const formData = JSON.parse(storedData);
  const userEmail = formData.email || '';
}
```

**Future State (When you add more fields)**:
```typescript
// Form component
const [formData, setFormData] = useState<UserFormData>({
  email: '',
  name: '',      // Future
  company: '',   // Future
});

// Token request
const metadata = {
  user_email: formData.email,
  user_name: formData.name,      // Future
  user_company: formData.company, // Future
};
```

**Don't change** to direct string storage because:
1. You'll need to refactor again when adding fields
2. Type safety is lost
3. More error-prone

---

## Additional Recommendations

### 1. Add TypeScript Interface for Metadata

Create a shared type for metadata structure:

```typescript
// types/metadata.ts (new file)
export interface ParticipantMetadata {
  user_email: string;
  session_start: string;
  // Future fields:
  // user_name?: string;
  // user_company?: string;
}
```

**Use in route.ts**:
```typescript
import { ParticipantMetadata } from '@/types/metadata';

const metadata: ParticipantMetadata = {
  user_email: userEmail,
  session_start: new Date().toISOString(),
};
```

**Benefits**:
- Type safety
- Autocomplete
- Catches errors at compile time
- Single source of truth

### 2. Add Logging for Debugging

```typescript
// In route.ts, after parsing body
console.log('Token request received:', {
  has_email: !!userEmail,
  email_domain: userEmail ? userEmail.split('@')[1] : null,
  timestamp: new Date().toISOString(),
});

// After creating token
console.log('Token created successfully:', {
  room: roomName,
  participant: participantIdentity,
  metadata_included: !!metadata.user_email,
});
```

**Benefits**:
- Easy debugging in production
- Can verify email flow
- Track patterns (which domains are calling)

### 3. Handle SessionStorage Edge Cases

```typescript
// useRoom.ts - More robust retrieval
let userEmail = '';
try {
  const storedData = sessionStorage.getItem('userFormData');
  if (storedData) {
    const formData = JSON.parse(storedData);
    userEmail = formData?.email || '';

    // Validate email format on frontend too
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (userEmail && !emailRegex.test(userEmail)) {
      console.warn('Invalid email in sessionStorage:', userEmail);
      userEmail = ''; // Clear invalid email
    }
  }
} catch (e) {
  console.warn('Could not retrieve user email from sessionStorage:', e);
}
```

---

## Implementation Checklist

### Frontend Changes
- [ ] Keep sessionStorage format as JSON object
- [ ] Retrieve email in `useRoom.ts` (add ~10 lines)
- [ ] Pass `user_email` in token request body
- [ ] Add error handling for sessionStorage parsing

### Backend Changes
- [ ] Accept `user_email` from request body
- [ ] Add email format validation (warn, don't fail)
- [ ] Create metadata object with `user_email` field
- [ ] Pass metadata to `createParticipantToken`
- [ ] Add logging for debugging

### Optional Improvements
- [ ] Create TypeScript interface for metadata
- [ ] Add detailed logging
- [ ] Add frontend email validation
- [ ] Add tests for token generation with metadata

---

## Testing Strategy

### 1. Valid Email Test
```typescript
// Test data
const validEmails = [
  'test@company.com',
  'user.name@subdomain.company.co.uk',
  'email+tag@domain.com',
];

// For each, verify:
// - Token created successfully
// - Metadata contains email
// - JWT decodes correctly
```

### 2. Invalid Email Test
```typescript
// Test data
const invalidEmails = [
  '',                    // Empty
  'notanemail',         // No @
  '@nodomain.com',      // No local part
  'user@',              // No domain
  'user @domain.com',   // Space
];

// For each, verify:
// - Token still created (graceful degradation)
// - Metadata contains empty string
// - Connection succeeds
```

### 3. Missing Email Test
```typescript
// Don't include user_email in request body
// Verify:
// - Token created successfully
// - Metadata contains empty string
// - Agent can still function
```

---

## Quick Reference

| Question | Answer | Rationale |
|----------|--------|-----------|
| **Field name?** | `user_email` | Standard convention, future-proof |
| **Add validation?** | Yes, warn-only | Graceful degradation, better UX |
| **Fail on invalid?** | No (warn only) | Session should work without email |
| **SessionStorage format?** | Keep JSON object | Future extensibility, type safety |
| **Add TypeScript types?** | Recommended | Type safety, better DX |

---

## Summary

**Implement these changes**:
1. Use `user_email` as field name consistently
2. Add email validation that warns but doesn't fail
3. Keep sessionStorage as JSON object
4. Add logging for debugging
5. (Optional) Add TypeScript interface

**Don't do these**:
1. Don't return 400 on invalid email
2. Don't change sessionStorage to string
3. Don't add complex validation logic

**Estimated time**: 20-30 minutes to implement all changes

---

**Ready to implement?** Yes! These answers should unblock all questions.

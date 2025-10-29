# Implementation Ready: Email Metadata for Voice Calls

Hi [Frontend Engineer],

Thanks for the detailed responses! I've analyzed your codebase and created the exact implementation. The email is already collected perfectly - we just need to pass it through to LiveKit.

## Summary of Changes Needed

**Total changes: 3 small modifications (~20 lines of code)**

### 1️⃣ Frontend: `hooks/useRoom.ts` (Add ~10 lines)
- Retrieve email from sessionStorage (which you already set)
- Pass it in the token request body

### 2️⃣ Backend: `app/api/connection-details/route.ts` (Add ~5 lines)
- Accept email from request body
- Add it to participant metadata in the token

### 3️⃣ Python Agent: `agent.py` (We'll handle this)
- Extract email from participant metadata
- Include in analytics export

## Your Part (Frontend Only)

I've created a complete implementation guide here:
**`EMAIL_METADATA_IMPLEMENTATION.md`**

The changes you need are in:
- **Section 1**: Frontend Changes (useRoom.ts)
- **Section 2**: Backend Changes (route.ts)

Each section shows:
- Current code (what you have now)
- Changed code (what to replace it with)
- The additions are marked with comments like `// ADD THIS`

## What This Accomplishes

```
Form (✅ already done)
  → SessionStorage (✅ already done)
    → Token Request (🔧 add email to body)
      → Token Generation (🔧 add email to metadata)
        → LiveKit Room (automatic)
          → Python Agent (we'll handle)
            → Analytics/Salesforce (we'll handle)
```

## Testing

After you make the changes:

1. **Quick Check**:
   - Open Network tab in DevTools
   - Start a call
   - Look for `/api/connection-details` request
   - Verify body contains: `"user_email": "test@example.com"`

2. **Token Check**:
   - Copy the `participantToken` from the response
   - Paste into https://jwt.io
   - Look for metadata field with email

## Timeline

- **Your changes**: ~15-20 minutes
- **Testing**: ~10 minutes
- **Our agent changes**: Already prepared
- **Full deployment**: Same day

## Questions Before You Start?

1. Do you want me to make a PR with these changes?
2. Any concerns about adding metadata to the token?
3. Preferred deployment schedule?

The implementation is straightforward - we're using LiveKit's standard metadata pattern. No breaking changes, fully backward compatible.

Let me know when you're ready to implement, or if you need any clarification!

---

**Implementation guide**: See `EMAIL_METADATA_IMPLEMENTATION.md` for complete code
**Testing guide**: Included in the implementation doc
**Rollback plan**: Each component can be reverted independently

Best,
[Your name]
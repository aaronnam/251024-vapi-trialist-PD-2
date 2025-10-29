# Frontend Implementation Questions - Voice Call Metadata

Hi! We're implementing email tracking for voice calls so we can match them to the right person in Salesforce. To do this flawlessly, I need to understand how your frontend form and LiveKit connection work.

**Please answer the questions below and return your answers in the "Response Format" section at the bottom of this file.**

---

## Section 1: Current Form Implementation

### Q1.1: What form fields do you currently collect?
**Why**: Need to know what data is available to pass through

**Response**:
```
[ ] Name
[ ] Email (business email)
[ ] Company
[ ] Phone
[ ] Other: _______________
```

### Q1.2: What is the exact field name/ID for the email input in your code?
**Why**: Need the precise variable name to use when passing to LiveKit

**Example**: `businessEmail`, `email`, `userEmail`, `contact_email`, etc.

**Response**: `_____________`

### Q1.3: Can you share the form submission handler code?
**Why**: Need to see how form data flows to the voice call connection

**Response**:
```javascript
// Paste your form submission code here (even if just a snippet)
```

---

## Section 2: LiveKit Connection Setup

### Q2.1: Where and how do you currently connect to LiveKit?
**Why**: Need to see the exact location and method to inject metadata

**Response**:
```javascript
// Paste the code where you call room.connect() or similar
// Show the complete connection flow, including:
// - How you get the token
// - What parameters you pass
// - The actual connection call
```

### Q2.2: What LiveKit client SDK version are you using?
**Why**: API signatures differ between versions

**Response**:
```
livekit-client version: _____________
Example: "livekit-client@2.1.0" or "latest" if unsure
```

### Q2.3: Are you currently passing ANY metadata when connecting?
**Why**: If yes, we need to add our email field to existing metadata, not replace it

**Response**:
```
[ ] No metadata currently
[ ] Yes, here's what we pass:
    [ ] Room metadata
    [ ] Participant metadata
    [ ] Connection options

Paste current metadata code:
____________________
```

---

## Section 3: Token Generation Backend

### Q3.1: What backend framework handles token generation?
**Why**: Different frameworks have different ways to modify the token

**Response**:
```
[ ] Next.js (API Routes)
[ ] Express.js
[ ] FastAPI (Python)
[ ] Node.js (other framework)
[ ] Other: _______________
```

### Q3.2: Can you share the token generation endpoint code?
**Why**: Need to see if we modify token generation or use connection options

**Response**:
```javascript
// Paste your token generation code
// Looking for: POST /api/token or similar endpoint
// Show the complete function, including how you use LiveKit SDK
```

### Q3.3: Are you using the LiveKit server SDK to create tokens?
**Why**: If yes, metadata can be baked into the token (more secure)

**Response**:
```
[ ] Yes, using LiveKit SDK (which one: Node.js, Go, Python, etc?)
[ ] No, creating tokens manually/differently
[ ] Not sure

Details: _______________
```

---

## Section 4: Data Flow & Architecture

### Q4.1: What is the exact user journey from form submission to voice call starting?
**Why**: Need to ensure email data is available at the right point

**Response**:
```
Step 1: _______________
Step 2: _______________
Step 3: _______________
Step 4: _______________

Example flow:
Step 1: User fills form with email, name, company
Step 2: Click "Start Call" button
Step 3: Frontend calls POST /api/token
Step 4: Backend returns token
Step 5: Frontend connects to LiveKit with token
Step 6: Voice call starts
```

### Q4.2: Is the form data still available when the LiveKit connection is initiated?
**Why**: If form is on a different page, we may need a different approach

**Response**:
```
[ ] Yes, same page/component - form data still in state
[ ] No, form is on a different page
[ ] Not sure

Details: _______________
```

### Q4.3: Do you redirect or navigate after form submission?
**Why**: If yes, we need to preserve form data between pages

**Response**:
```
[ ] No redirect - everything happens on same page
[ ] Yes, redirect to: _______________
[ ] URL parameters with data? (yes/no)
[ ] Local storage? (yes/no)
[ ] Session storage? (yes/no)
```

---

## Section 5: Tech Stack Details

### Q5.1: What frontend framework are you using?
**Why**: Different patterns for different frameworks

**Response**:
```
[ ] React
[ ] Vue
[ ] Svelte
[ ] Vanilla JavaScript
[ ] Other: _______________
```

### Q5.2: Are you using TypeScript?
**Why**: Type definitions differ

**Response**:
```
[ ] Yes, TypeScript
[ ] No, JavaScript
```

### Q5.3: Do you have any state management?
**Why**: Form data might live in Redux, Zustand, Context, etc.

**Response**:
```
[ ] No state management
[ ] React Context
[ ] Redux
[ ] Zustand
[ ] Other: _______________

How is form data stored? _______________
```

---

## Section 6: Frontend Repository Details

### Q6.1: Where is the frontend code located?
**Why**: Help me navigate your repo structure

**Response**:
```
Frontend directory: _______________
Form component file: _______________
LiveKit connection file: _______________
Token endpoint file: _______________
```

### Q6.2: Can you provide the GitHub/repo link or directory path?
**Why**: Can look at code directly if needed

**Response**:
```
_______________
```

---

## Section 7: Current Constraints & Considerations

### Q7.1: Any existing user identification system?
**Why**: If users are authenticated, we might have email from user account instead of form

**Response**:
```
[ ] No authentication system
[ ] User accounts / authentication exists
[ ] Get email from: _______________
```

### Q7.2: Does the same user ever call multiple times?
**Why**: Affects how we match to Salesforce

**Response**:
```
[ ] No, one-time trials only
[ ] Yes, users can call multiple times
[ ] Not sure
```

### Q7.3: Do you have any existing integrations we should know about?
**Why**: Might already be passing metadata somewhere

**Response**:
```
Currently passing to:
[ ] Salesforce
[ ] Amplitude
[ ] Other analytics: _______________
[ ] Nothing

Details: _______________
```

---

## Quick Reference: What We're Trying to Do

We want to:
1. Capture the user's business email from the form
2. Pass it to the LiveKit room when they connect
3. Retrieve it in the Python agent (backend)
4. Include it in the analytics export to S3
5. Use it to match to the right Salesforce Lead/Contact

**The minimal addition**: One line in your frontend to pass email → One line in your backend to accept it → One line in our agent to read it.

---

## Response Format

Please fill out your answers below using the exact format shown. This helps me parse and implement the solution quickly.

```
FRONTEND ENGINEER RESPONSE
================================

Q1.1 - Form Fields:
[ Answer here ]

Q1.2 - Email Field Name:
[ Answer here ]

Q1.3 - Form Submission Code:
[ Answer here ]

Q2.1 - LiveKit Connection Code:
[ Answer here ]

Q2.2 - SDK Version:
[ Answer here ]

Q2.3 - Current Metadata:
[ Answer here ]

Q3.1 - Backend Framework:
[ Answer here ]

Q3.2 - Token Generation Code:
[ Answer here ]

Q3.3 - Using LiveKit Server SDK:
[ Answer here ]

Q4.1 - User Journey:
[ Answer here ]

Q4.2 - Form Data Available at Connection:
[ Answer here ]

Q4.3 - Redirects/Navigation:
[ Answer here ]

Q5.1 - Frontend Framework:
[ Answer here ]

Q5.2 - TypeScript:
[ Answer here ]

Q5.3 - State Management:
[ Answer here ]

Q6.1 - Frontend Code Locations:
[ Answer here ]

Q6.2 - GitHub/Repo Link:
[ Answer here ]

Q7.1 - Authentication System:
[ Answer here ]

Q7.2 - Multiple Calls Per User:
[ Answer here ]

Q7.3 - Existing Integrations:
[ Answer here ]
```

---

## Next Steps

Once I receive your answers:

1. **Day 1**: I'll provide exact code changes (frontend + backend)
2. **Day 2**: We'll implement and test
3. **Day 3**: Email will flow from form → LiveKit → Agent → Analytics → Ready for Salesforce

**Questions?** Ask before responding - I'd rather clarify than implement incorrectly.

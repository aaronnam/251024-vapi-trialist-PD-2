# Voice Call Metadata Implementation - Frontend Analysis

## Executive Summary

Email is currently collected and stored in `sessionStorage` but **NOT passed to LiveKit** or the agent. This document provides a complete audit of your frontend implementation and identifies exactly what needs to change.

---

## Complete Responses to Implementation Questions

### Section 1: Current Form Implementation

#### Q1.1: Form Fields Currently Collected
- [x] Email (business email only)
- [ ] Name
- [ ] Company
- [ ] Phone

#### Q1.2: Email Field Name/ID
**Variable name**: `email`

**Location**: `components/app/welcome-view.tsx:25-26`

```typescript
const [formData, setFormData] = useState<UserFormData>({
  email: '',
});
```

#### Q1.3: Form Submission Handler

**Location**: `components/app/welcome-view.tsx:63-67`

```typescript
const handleStartCall = () => {
  // Store form data in sessionStorage or send to backend
  sessionStorage.setItem('userFormData', JSON.stringify(formData));
  onStartCall();
};
```

**Email Input Implementation** (lines 93-115):
```typescript
<input
  type="email"
  placeholder="Business email"
  value={formData.email}
  onChange={handleChange('email')}
  onBlur={handleBlur('email')}
  className={cn(
    'w-full px-3.5 py-2.5 text-sm',
    'bg-background rounded-lg border',
    // ... styling
  )}
/>
{errors.email && touched.email && (
  <p className="text-destructive mt-1 pl-1 text-left text-xs">{errors.email}</p>
)}
```

**Validation**:
```typescript
const isFormValid = useMemo(() => {
  return formData.email.trim() !== '' && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email);
}, [formData]);
```

---

### Section 2: LiveKit Connection Setup

#### Q2.1: LiveKit Connection Code

**Primary Connection Flow**: `hooks/useRoom.ts:71-101`

```typescript
const startSession = useCallback(() => {
  setIsSessionActive(true);

  if (room.state === 'disconnected') {
    const { isPreConnectBufferEnabled } = appConfig;
    Promise.all([
      room.localParticipant.setMicrophoneEnabled(true, undefined, {
        preConnectBuffer: isPreConnectBufferEnabled,
      }),
      tokenSource
        .fetch({ agentName: appConfig.agentName })
        .then((connectionDetails) =>
          room.connect(connectionDetails.serverUrl, connectionDetails.participantToken)
        ),
    ]).catch((error) => {
      if (aborted.current) {
        return;
      }

      toastAlert({
        title: 'There was an error connecting to the agent',
        description: `${error.name}: ${error.message}`,
      });
    });
  }
}, [room, appConfig, tokenSource]);
```

**Token Fetching** (lines 39-69):

```typescript
const tokenSource = useMemo(
  () =>
    TokenSource.custom(async () => {
      const url = new URL(
        process.env.NEXT_PUBLIC_CONN_DETAILS_ENDPOINT ?? '/api/connection-details',
        window.location.origin
      );

      try {
        const res = await fetch(url.toString(), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Sandbox-Id': appConfig.sandboxId ?? '',
          },
          body: JSON.stringify({
            room_config: appConfig.agentName
              ? {
                  agents: [{ agent_name: appConfig.agentName }],
                }
              : undefined,
          }),
        });
        return await res.json();
      } catch (error) {
        console.error('Error fetching connection details:', error);
        throw new Error('Error fetching connection details!');
      }
    }),
  [appConfig]
);
```

#### Q2.2: LiveKit Client SDK Version

```json
{
  "livekit-client": "^2.15.8",
  "livekit-server-sdk": "^2.13.2"
}
```

#### Q2.3: Current Metadata Being Passed

**[x] No metadata currently**

Currently, **NO** participant metadata or attributes are being passed:
- No room metadata
- No participant metadata
- No connection options beyond agent dispatch

Email is stored in `sessionStorage` but never sent to LiveKit.

---

### Section 3: Token Generation Backend

#### Q3.1: Backend Framework

**[x] Next.js (API Routes)**

#### Q3.2: Token Generation Endpoint Code

**File**: `app/api/connection-details/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { AccessToken, type AccessTokenOptions, type VideoGrant } from 'livekit-server-sdk';

type ConnectionDetails = {
  serverUrl: string;
  roomName: string;
  participantName: string;
  participantToken: string;
};

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

export const revalidate = 0;

export async function POST() {
  try {
    if (LIVEKIT_URL === undefined) {
      throw new Error('LIVEKIT_URL is not defined');
    }
    if (API_KEY === undefined) {
      throw new Error('LIVEKIT_API_KEY is not defined');
    }
    if (API_SECRET === undefined) {
      throw new Error('LIVEKIT_API_SECRET is not defined');
    }

    // Generate unique room name for each PandaDoc trial session
    const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;

    // Generate participant identity for trialist
    const participantIdentity = `trialist_${Date.now()}`;
    const participantName = 'PandaDoc Trialist';

    const participantToken = await createParticipantToken(
      { identity: participantIdentity, name: participantName },
      roomName
    );

    // Return connection details
    const data: ConnectionDetails = {
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: participantToken,
      participantName,
    };
    const headers = new Headers({
      'Cache-Control': 'no-store',
    });
    return NextResponse.json(data, { headers });
  } catch (error) {
    if (error instanceof Error) {
      console.error(error);
      return new NextResponse(error.message, { status: 500 });
    }
  }
}

function createParticipantToken(userInfo: AccessTokenOptions, roomName: string): Promise<string> {
  const at = new AccessToken(API_KEY, API_SECRET, {
    ...userInfo,
    ttl: '30m', // 30 minute sessions for trialists
  });
  const grant: VideoGrant = {
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  };
  at.addGrant(grant);

  return at.toJwt();
}
```

#### Q3.3: Using LiveKit Server SDK

**[x] Yes, using LiveKit SDK (Node.js)**

- **SDK**: `livekit-server-sdk@2.13.2`
- **Method**: Using `AccessToken` class to create JWT tokens
- **What's available**: Can add attributes/metadata to token via AccessToken options

---

### Section 4: Data Flow & Architecture

#### Q4.1: User Journey (Step-by-Step)

1. **User fills form**: Email entered on welcome page (`WelcomeView` component)
2. **Email validated**: Client-side regex validation against pattern `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
3. **User clicks button**: "Start Trial Assistance" button calls `handleStartCall()`
4. **Data stored**: Email saved to `sessionStorage` as `userFormData` JSON string
5. **Session starts**: `onStartCall()` callback triggers `startSession()` in `useRoom.ts`
6. **Token request**: Frontend calls `POST /api/connection-details` with room config
7. **Token generation**: Backend creates AccessToken without email metadata
8. **Connection**: Frontend connects to LiveKit using token
9. **Call starts**: Voice call begins

#### Q4.2: Form Data Availability at Connection Time

**[x] Yes, same page/component - form data still in state**

- Form data remains in `sessionStorage` throughout the session
- Email is available when `startSession()` is called
- Email is NOT currently passed to the token endpoint or LiveKit

#### Q4.3: Redirects/Navigation

**[x] No redirect - everything happens on same page**

- [x] Session storage used: `sessionStorage.setItem('userFormData', JSON.stringify(formData))`
- [ ] URL parameters: No
- [ ] Local storage: No

**Data persistence**: Email survives across component re-renders and remains available for the entire session.

---

### Section 5: Tech Stack Details

#### Q5.1: Frontend Framework

**[x] React** (specifically Next.js)

- **Version**: Next.js 15.5.2
- **React Version**: 19.0.0
- **Architecture**: App Router (Next.js 15)

#### Q5.2: TypeScript

**[x] Yes, TypeScript**

- **Version**: `typescript@^5`
- **Strict mode**: Enabled by default in Next.js projects

#### Q5.3: State Management

**[x] React Context** (primary)

**Form Data Storage**:
- **Component level**: `useState()` in `WelcomeView` component
- **Session level**: `sessionStorage` for persistence between component lifecycles
- **App level**: `SessionProvider` using React Context for session state
- **LiveKit state**: `RoomContext` from `@livekit/components-react`

**No Redux, Zustand, or other state management library used.**

---

### Section 6: Frontend Repository Details

#### Q6.1: Code Locations

| Component | Path |
|-----------|------|
| Frontend directory | `/Users/aaron.nam/Desktop/Repos/frontend-ui/pandadoc-voice-ui/` |
| Form component | `components/app/welcome-view.tsx` |
| LiveKit connection | `hooks/useRoom.ts` |
| Token endpoint | `app/api/connection-details/route.ts` |
| Session provider | `components/app/session-provider.tsx` |
| View controller | `components/app/view-controller.tsx` |
| Main app | `components/app/app.tsx` |

#### Q6.2: Repository Link

```
Local path: /Users/aaron.nam/Desktop/Repos/frontend-ui
```

---

### Section 7: Current Constraints & Considerations

#### Q7.1: Authentication System

**[x] No authentication system**

- Anonymous trialists only
- Participant identity generated as: `trialist_${Date.now()}`
- Email collected but not used for authentication
- No user accounts or login system

#### Q7.2: Multiple Calls Per User

**[x] Yes, technically possible but not tracked**

- Each call generates a new room and participant identity
- No correlation between calls from the same user
- Email is the only identifier linking calls to a person

#### Q7.3: Existing Integrations

**[x] Nothing currently**

- No Salesforce integration
- No Amplitude or analytics tracking
- No existing metadata pipeline
- Email collected but not exported

---

## Current Implementation Gap

### What Works ✅
- Email form collection with validation
- sessionStorage persistence
- LiveKit token generation
- Connection to agent

### What's Missing ❌
- Email is **NOT sent** to token endpoint
- Email is **NOT added** to participant token/metadata
- Email is **NOT available** to Python agent
- Email is **NOT exported** for Salesforce matching

---

## Implementation Requirements for Email Tracking

To make email flow from form → LiveKit → Agent → Analytics → Salesforce, you need:

### Frontend Changes (useRoom.ts)
- Retrieve email from sessionStorage
- Pass email to token endpoint in request body

### Backend Changes (route.ts)
- Accept email in request body
- Add email to participant attributes in AccessToken

### Token Changes
- Include email as participant metadata accessible to agent

### Agent Changes (Python - not in this repo)
- Read participant metadata
- Include email in analytics export

---

## Quick Reference: File Locations

```
Frontend-UI Root
├── pandadoc-voice-ui/
│   ├── components/
│   │   └── app/
│   │       ├── welcome-view.tsx          ← Email form (L63-67: handleStartCall)
│   │       ├── session-provider.tsx       ← Context setup
│   │       ├── view-controller.tsx        ← View routing
│   │       └── app.tsx                    ← Main app wrapper
│   ├── hooks/
│   │   └── useRoom.ts                     ← LiveKit connection (L71-101: startSession)
│   ├── app/
│   │   └── api/
│   │       └── connection-details/
│   │           └── route.ts               ← Token generation endpoint
│   ├── app-config.ts                      ← App configuration
│   └── package.json                       ← Dependencies
└── docs/
    └── VOICE_CALL_METADATA_IMPLEMENTATION.md  ← This file
```

---

## Next Steps

Ready to implement?

1. **Modify `useRoom.ts`**: Pass email from sessionStorage to token endpoint
2. **Modify `route.ts`**: Accept email and add to participant metadata
3. **Test locally**: Verify email flows through connection
4. **Deploy**: Push changes to production
5. **Agent integration**: Agent can read email from participant metadata

**Estimated time**: 15-30 minutes for minimal viable implementation

---

**Document generated**: 2025-10-29
**Analysis completed**: Frontend codebase audit complete and ready for implementation

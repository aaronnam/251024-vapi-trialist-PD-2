# User Information Form Analysis
## Adding Email, Name, and Company Collection to Voice Agent UI

### Executive Summary

Should we add a user information form (email, name, company) before allowing voice agent access? This analysis explores implementation approaches, trade-offs, and provides a recommendation.

**Recommendation**: Build the current implementation first (Phase 1), then add the form as an enhancement (Phase 2). This provides faster MVP delivery, simpler initial testing, and flexibility to adjust based on user feedback.

---

## Business Context

### Why Collect This Information?

1. **Lead Generation**
   - Capture qualified leads for sales follow-up
   - Track trial engagement by company
   - Enable multi-touch nurture campaigns

2. **Personalization**
   - Agent can greet users by name
   - Provide company-specific examples
   - Remember user across sessions

3. **Analytics & Attribution**
   - Track usage patterns by company size
   - Measure conversion from voice interaction to paid
   - Understand which companies engage most

4. **Qualification**
   - Pre-qualify based on email domain
   - Route enterprise domains differently
   - Block competitors or spam

5. **Compliance**
   - Consent for recording/data processing
   - GDPR/privacy requirements
   - Terms of service acceptance

### Trade-offs

| Aspect | With Form | Without Form |
|--------|-----------|--------------|
| **Conversion** | Lower (friction) | Higher (instant access) |
| **Lead Quality** | High (verified emails) | None (anonymous) |
| **Personalization** | Full (name, company context) | Limited (generic) |
| **Time to First Value** | Slower (form filling) | Instant (one click) |
| **Implementation Complexity** | Higher | Lower |
| **Data Collection** | Immediate | Must add later |

---

## Implementation Approaches

### Option A: Build Current Spec First, Add Form Later (RECOMMENDED ✅)

**Phase 1: Current Implementation (Days 1-3)**
- One-click voice connection
- Anonymous users
- Focus on core voice functionality
- Validate LiveKit integration

**Phase 2: Add Form Enhancement (Days 4-5)**
- Add pre-connection form
- Progressive disclosure (optional → required)
- A/B test conversion impact

**Pros:**
- ✅ Faster MVP (3 days vs 5 days)
- ✅ Simpler initial debugging
- ✅ Validate core value prop first
- ✅ Flexibility to adjust requirements
- ✅ Can A/B test with/without form
- ✅ Lower initial complexity

**Cons:**
- ❌ No lead capture initially
- ❌ Some refactoring needed later
- ❌ Early users remain anonymous

### Option B: Include Form from Start

**Single Phase (Days 1-5)**
- Build form + voice agent together
- Required fields from day one
- Full personalization immediately

**Pros:**
- ✅ Complete solution from start
- ✅ Lead capture from day one
- ✅ No refactoring needed
- ✅ Full personalization immediately

**Cons:**
- ❌ Longer time to MVP
- ❌ Higher initial complexity
- ❌ More friction for users
- ❌ Can't validate core functionality quickly
- ❌ No A/B testing opportunity

### Option C: Hybrid - Optional Form Initially

**Phase 1 (Days 1-4)**
- Build form UI but make it optional
- "Skip for now" button
- Track skip vs fill rates

**Phase 2 (Later)**
- Make required based on data
- Remove skip option if needed

**Pros:**
- ✅ Best of both worlds
- ✅ Data-driven decision
- ✅ Progressive enhancement

**Cons:**
- ❌ More complex than Option A
- ❌ Still delays MVP slightly

---

## Technical Implementation Details

### Frontend Changes Required

#### 1. Form Component

```tsx
// components/UserInfoForm.tsx
interface UserInfo {
  email: string;
  firstName: string;
  lastName: string;
  company: string;
  consent: boolean;
}

export function UserInfoForm({ onSubmit }: { onSubmit: (info: UserInfo) => void }) {
  const [errors, setErrors] = useState({});

  return (
    <form className="user-info-form">
      <h2>Start Your PandaDoc Voice Session</h2>
      <p>Tell us a bit about yourself to personalize your experience</p>

      <input
        type="email"
        placeholder="Work email*"
        required
        pattern="^[^@]+@[^@]+\.[^@]+$"
      />

      <div className="name-row">
        <input type="text" placeholder="First name*" required />
        <input type="text" placeholder="Last name*" required />
      </div>

      <input type="text" placeholder="Company*" required />

      <label className="consent">
        <input type="checkbox" required />
        I agree to PandaDoc's terms and consent to call recording
      </label>

      <button type="submit" className="primary">
        Start Voice Session
      </button>

      {/* Option C: Skip button */}
      <button type="button" className="secondary">
        Skip for now
      </button>
    </form>
  );
}
```

#### 2. State Management

```tsx
// lib/user-context.tsx
const UserContext = createContext<UserInfo | null>(null);

export function useUser() {
  const context = useContext(UserContext);
  return context;
}

// Persist to localStorage
function persistUser(user: UserInfo) {
  localStorage.setItem('pandadoc-voice-user', JSON.stringify(user));
}

function loadUser(): UserInfo | null {
  const stored = localStorage.getItem('pandadoc-voice-user');
  return stored ? JSON.parse(stored) : null;
}
```

#### 3. Modified Connection Flow

```tsx
// app/(app)/page.tsx
function VoiceAgentPage() {
  const [user, setUser] = useState<UserInfo | null>(loadUser());
  const [showForm, setShowForm] = useState(!user);

  if (showForm) {
    return (
      <UserInfoForm
        onSubmit={(info) => {
          setUser(info);
          persistUser(info);
          setShowForm(false);
        }}
      />
    );
  }

  // Regular voice agent UI
  return <VoiceAgent user={user} />;
}
```

### Backend Changes Required

#### 1. Enhanced Token Endpoint

```typescript
// app/api/connection-details/route.ts
export async function POST(request: Request) {
  const body = await request.json();
  const { room_config, user_info } = body;

  // Generate identity from user info
  const identity = user_info
    ? `${user_info.firstName}_${user_info.lastName}_${Date.now()}`
    : `guest_${Date.now()}`;

  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity,
      ttl: '30m',
      roomJoin: true,
      room: roomName,
      // Pass user info as metadata
      metadata: JSON.stringify(user_info || {}),
    }
  );

  // ... rest of token generation
}
```

### Agent Changes Required

#### 1. Access User Information

```python
# my-app/src/agent.py
class PandaDocTrialistAgent(Agent):
    async def on_participant_connected(self, participant):
        # Parse user metadata
        metadata = json.loads(participant.metadata or '{}')

        self.user_email = metadata.get('email')
        self.user_name = metadata.get('firstName')
        self.company = metadata.get('company')

        # Update greeting
        if self.user_name:
            self.greeting = f"Hi {self.user_name}! This is Sarah from PandaDoc..."
        else:
            self.greeting = "Hi! This is Sarah from PandaDoc..."
```

---

## Implementation Timeline

### Approach A: Phased (RECOMMENDED)

```
Day 1-3: Build current spec (no form)
  ├─ Day 1: Setup and configuration
  ├─ Day 2: Agent integration and UI
  └─ Day 3: Testing and deployment

Day 4-5: Add form enhancement
  ├─ Day 4: Build form component and validation
  └─ Day 5: Integrate with token endpoint and agent

Total: 5 days (but MVP in 3 days)
```

### Approach B: All-at-once

```
Day 1-5: Build complete solution
  ├─ Day 1: Setup and configuration
  ├─ Day 2: Build form UI and validation
  ├─ Day 3: Token endpoint modifications
  ├─ Day 4: Agent integration with personalization
  └─ Day 5: Testing and deployment

Total: 5 days (no MVP until day 5)
```

---

## Form Design Best Practices

### 1. Minimize Friction

```tsx
// Smart defaults and auto-complete
<input
  type="email"
  autoComplete="email"
  placeholder="name@company.com"
/>

// Company detection from email
function detectCompany(email: string) {
  const domain = email.split('@')[1];
  // Remove common suffixes
  return domain?.replace(/\.(com|io|co|net|org)$/, '');
}
```

### 2. Progressive Disclosure

```tsx
// Start with just email
const [step, setStep] = useState(1);

if (step === 1) {
  return <EmailStep onNext={(email) => setStep(2)} />;
}

if (step === 2) {
  return <DetailsStep email={email} onComplete={handleComplete} />;
}
```

### 3. Social Proof

```tsx
<div className="social-proof">
  <p>✓ Join 50,000+ businesses using PandaDoc</p>
  <p>✓ No credit card required</p>
  <p>✓ 2-minute personalized demo</p>
</div>
```

### 4. Error Handling

```tsx
// Friendly validation messages
const errors = {
  email: "Please use your work email",
  firstName: "We'd love to know your name",
  company: "Help us customize your experience",
};

// Validate on blur, not on type
<input onBlur={validateEmail} />
```

---

## Conversion Impact Analysis

### Expected Conversion Rates

| Scenario | Estimated Conversion | Lead Volume | Lead Quality |
|----------|---------------------|-------------|--------------|
| No form | 15-20% | 0 | N/A |
| Optional form | 12-15% (5% fill) | Low | High |
| Required form | 5-8% | Medium | High |
| Progressive (email → details) | 8-12% | Medium | Medium |

### Metrics to Track

1. **Form Metrics**
   - Start rate (view form)
   - Completion rate
   - Field drop-off rates
   - Time to complete

2. **Voice Session Metrics**
   - Sessions started
   - Average duration
   - Qualification rate
   - Return user rate

3. **Business Metrics**
   - Lead to opportunity conversion
   - Voice session to trial conversion
   - Trial to paid conversion

---

## Security & Privacy Considerations

### Data Collection

```typescript
// Implement proper consent
interface ConsentOptions {
  marketing: boolean;  // Optional
  recording: boolean;  // Required for voice
  analytics: boolean;  // Required
}

// GDPR compliance
const gdprCountries = ['DE', 'FR', 'IT', ...];
if (gdprCountries.includes(userCountry)) {
  showGDPRConsent();
}
```

### Data Storage

```typescript
// Don't store sensitive data client-side
// Only store non-sensitive for convenience
localStorage.setItem('user-session', {
  firstName: user.firstName,  // OK
  hasAccount: true,           // OK
  // email: user.email,        // Don't store
  // company: user.company,    // Don't store
});
```

---

## Recommendations

### Start with Approach A (Phased Implementation)

**Week 1:**
1. Build and deploy current spec (no form)
2. Start collecting anonymous usage data
3. Validate core voice functionality

**Week 2:**
1. Design and implement form
2. Deploy as optional (A/B test)
3. Measure conversion impact

**Week 3:**
1. Analyze data
2. Decide on required vs optional
3. Optimize based on drop-off points

### Form Fields Priority

**Must Have (Phase 1):**
- Work email
- First name
- Consent checkbox

**Nice to Have (Phase 2):**
- Last name
- Company name
- Phone number
- Company size

**Future (Phase 3):**
- Role/title
- Use case
- Current tools

### Success Criteria

**Phase 1 Success (No Form):**
- [ ] 100+ voice sessions started
- [ ] >2 min average duration
- [ ] <5% error rate
- [ ] Core functionality validated

**Phase 2 Success (With Form):**
- [ ] <30% conversion drop
- [ ] 50+ qualified leads captured
- [ ] Personalization working
- [ ] Positive user feedback

---

## Implementation Checklist

### Phase 1: Core Voice Agent (Days 1-3)

- [ ] Clone agent-starter-react
- [ ] Configure LiveKit credentials
- [ ] Add PandaDoc branding
- [ ] Test voice connection
- [ ] Deploy to production
- [ ] Add analytics tracking

### Phase 2: User Form (Days 4-5)

- [ ] Design form UI/UX
- [ ] Build form component
- [ ] Add validation logic
- [ ] Implement localStorage persistence
- [ ] Enhance token endpoint
- [ ] Update agent greeting logic
- [ ] Add skip option (optional)
- [ ] Test form flow
- [ ] Deploy and monitor

### Phase 3: Optimization (Week 2+)

- [ ] A/B test required vs optional
- [ ] Optimize field order
- [ ] Add progressive disclosure
- [ ] Implement email domain detection
- [ ] Add social proof elements
- [ ] Monitor conversion metrics

---

## Conclusion

**Recommended Path:**

1. **Build current spec first** (3 days)
   - Get MVP live quickly
   - Validate core value proposition
   - Simplify initial debugging

2. **Add form as enhancement** (2 days)
   - Start with optional form
   - A/B test impact
   - Make required if business needs justify friction

3. **Optimize based on data** (ongoing)
   - Monitor conversion funnels
   - Reduce form friction
   - Balance lead quality vs quantity

This approach provides maximum flexibility while ensuring you can capture leads when ready. The phased implementation reduces risk and allows data-driven decisions about the optimal user experience.

**The key insight**: It's easier to add friction later than to remove it. Start simple, measure everything, and enhance based on real user behavior rather than assumptions.
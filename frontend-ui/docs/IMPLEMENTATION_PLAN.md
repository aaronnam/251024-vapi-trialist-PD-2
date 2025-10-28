# Frontend UI Implementation Plan
## Step-by-Step Guide to Deploy PandaDoc Voice Agent Web Interface

### Prerequisites Checklist
- [ ] Node.js 18+ installed
- [ ] LiveKit Cloud account with deployed agent
- [ ] LiveKit API credentials (key, secret, URL)
- [ ] Git installed
- [ ] Code editor (VS Code recommended)

---

## Phase 1: Initial Setup (30 minutes)

### Step 1.1: Clone the Starter Template
```bash
cd frontend-ui
git clone https://github.com/livekit-examples/agent-starter-react.git pandadoc-voice-ui
cd pandadoc-voice-ui
```

### Step 1.2: Install Dependencies
```bash
npm install
# or
pnpm install
```

### Step 1.3: Get LiveKit Credentials
```bash
# Option 1: Using LiveKit CLI (recommended)
lk cloud auth
lk app env -w -d .env.local

# Option 2: Manual creation
# Create .env.local file with your credentials
```

### Step 1.4: Verify Basic Setup
```bash
npm run dev
# Open http://localhost:3000
# Should see the default agent interface
```

**Checkpoint**: Default UI loads without errors ✓

---

## Phase 2: Configuration & Branding (45 minutes)

### Step 2.1: Update App Configuration
Edit `app-config.ts`:
```typescript
export const appConfig: AppConfig = {
  // Update company branding
  companyName: "PandaDoc",
  pageTitle: "PandaDoc Trial Success Assistant",
  pageDescription: "Your personal guide to PandaDoc success",

  // Update agent configuration
  agentName: "pd-voice-trialist-2-agent", // Your deployed agent name

  // Update visual branding
  logo: "path/to/pandadoc-logo.svg",
  accent: "#24856F", // PandaDoc Emerald Primary
  accentDark: "#1d6a59",

  // Configure features
  supportsChatInput: false,  // Voice-only for now
  supportsVideoInput: false,  // No video needed
  supportsScreenShare: false, // Can enable later
  isPreConnectBufferEnabled: true,

  // Update UI text
  startButtonText: "Start Trial Assistance",
  agents: {
    agent: {
      displayName: "PandaDoc Assistant",
      description: "I'll help you get the most from your trial",
      avatarText: "PD"
    }
  }
};
```

### Step 2.2: Add PandaDoc Logo
```bash
# Copy your logo to public folder
cp /path/to/pandadoc-logo.svg public/
# Update references in app-config.ts
```

### Step 2.3: Create Environment Configuration
Create `.env.local`:
```bash
# LiveKit credentials (from LiveKit Cloud)
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxx

# Optional: Analytics
NEXT_PUBLIC_AMPLITUDE_KEY=your-amplitude-key
```

### Step 2.4: Test Configuration Changes
```bash
npm run dev
# Verify branding appears correctly
# Verify "Start Trial Assistance" button works
```

**Checkpoint**: Branded UI with correct configuration ✓

---

## Phase 3: Agent Integration (45 minutes)

### Step 3.1: Update Connection Details Endpoint
Edit `app/api/connection-details/route.ts`:
```typescript
export async function POST(request: Request) {
  const { room_config } = await request.json();

  // Generate unique room name for each session
  const roomName = `pandadoc_trial_${Date.now()}_${Math.random().toString(36).substring(7)}`;

  // Create token with agent configuration
  const at = new AccessToken(
    process.env.LIVEKIT_API_KEY,
    process.env.LIVEKIT_API_SECRET,
    {
      identity: `trialist_${Date.now()}`, // Anonymous trialist
      ttl: '30m', // 30 minute sessions
      roomJoin: true,
      room: roomName,
    }
  );

  // Configure permissions
  at.addGrant({
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
    room: roomName,
  });

  // Add agent configuration
  if (room_config?.agents?.[0]?.agent_name) {
    const roomConfig = new RoomConfiguration(
      roomName,
      [], // No specific entry points needed
      [{
        agent_name: 'pd-voice-trialist-2-agent', // Your agent name
      }]
    );
    at.metadata = roomConfig.toJSON();
  }

  return Response.json({
    url: process.env.LIVEKIT_URL,
    token: at.toJwt(),
    room_name: roomName
  });
}
```

**Note on Agent Voice Responses:** Voice prompts and greetings are controlled by your LiveKit agent backend (the Python code in `my-app/src/agent.py`), not by the frontend. The frontend's only job is connecting the user's audio to the agent. All conversation content, personalization, and voice responses come from the agent itself. This keeps concerns separated and makes it easy to update agent behavior without touching the frontend code.

### Step 3.2: Test Agent Connection
```bash
# Ensure your agent is deployed to LiveKit Cloud
lk agent list

# Start the frontend
npm run dev

# Test the connection:
# 1. Click "Start Trial Assistance"
# 2. Allow microphone access
# 3. Speak to the agent
# 4. Verify agent responds
```

**Checkpoint**: Agent responds to voice input ✓

---

## Phase 4: UI Enhancements (45 minutes)

### Step 4.1: Customize Voice Visualizer
Edit `app/ui/VoiceVisualizer.tsx`:
```typescript
export function VoiceVisualizer({ state, audioTrack }) {
  return (
    <BarVisualizer
      state={state}
      barCount={7}  // More bars for better visual
      trackRef={audioTrack}
      style={{
        container: {
          padding: '2rem',
          background: 'rgba(36, 133, 111, 0.1)', // PandaDoc Emerald tint
          borderRadius: '12px',
        },
        bar: {
          backgroundColor: '#24856F', // PandaDoc Emerald Primary
        }
      }}
    />
  );
}
```

### Step 4.2: Add Connection Status Indicator
Create `app/ui/ConnectionStatus.tsx`:
```typescript
export function ConnectionStatus({ state }) {
  const statusMessages = {
    initializing: 'Connecting to assistant...',
    listening: 'Listening',
    thinking: 'Processing your request...',
    speaking: 'Speaking',
    disconnected: 'Connection lost'
  };

  return (
    <div className="connection-status">
      <span className={`status-dot ${state}`} />
      <span>{statusMessages[state] || 'Ready'}</span>
    </div>
  );
}
```

### Step 4.3: Add Transcript Display (Optional)
```typescript
// In main page component
const [transcript, setTranscript] = useState<string[]>([]);

// Subscribe to transcription events
useEffect(() => {
  room.on(RoomEvent.DataReceived, (payload) => {
    if (payload.topic === 'transcription') {
      setTranscript(prev => [...prev, payload.data]);
    }
  });
}, [room]);
```

**Checkpoint**: Enhanced UI with visual feedback ✓

---

## Phase 5: Testing & Validation (30 minutes)

### Step 5.1: Functional Testing Checklist
- [ ] User can start a call
- [ ] Microphone permissions requested
- [ ] Agent connects within 3 seconds
- [ ] Voice is clear both ways
- [ ] Visual feedback works
- [ ] Call can be ended cleanly
- [ ] Reconnection works after disconnect

### Step 5.2: Browser Compatibility Testing
Test on:
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Edge (latest)

### Step 5.3: Performance Testing
```bash
# Run Lighthouse audit
npm run build
npm run start
# Open Chrome DevTools > Lighthouse
# Run performance audit
```

Target metrics:
- First Contentful Paint: <1.5s
- Time to Interactive: <3s
- Connection time: <2s

**Checkpoint**: All tests passing ✓

---

## Phase 6: Deployment (30 minutes)

### Step 6.1: Prepare for Production
```bash
# Update environment variables for production
cp .env.local .env.production.local
# Edit with production credentials
```

### Step 6.2: Deploy to Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Follow prompts:
# - Link to existing project or create new
# - Set environment variables in Vercel dashboard
# - Deploy to production
```

### Step 6.3: Configure Custom Domain (Optional)
```bash
# In Vercel dashboard:
# 1. Go to Settings > Domains
# 2. Add your domain (e.g., voice.pandadoc.com)
# 3. Update DNS records as instructed
```

### Step 6.4: Post-Deployment Verification
- [ ] Production URL loads
- [ ] Agent connects successfully
- [ ] No console errors
- [ ] SSL certificate valid
- [ ] Monitoring alerts configured

**Checkpoint**: Live in production ✓

---

## Phase 7: Monitoring & Maintenance

### Setup Monitoring
```typescript
// Add to app/lib/analytics.ts
export function trackEvent(event: string, properties?: any) {
  // Amplitude tracking
  if (window.amplitude) {
    window.amplitude.track(event, properties);
  }

  // Console logging for development
  console.log('Event:', event, properties);
}

// Track key events
trackEvent('call_started', { agent: 'pd-voice-trialist-2' });
trackEvent('call_ended', { duration: callDuration });
trackEvent('error', { type: errorType, message: errorMessage });
```

### Regular Maintenance Tasks
- Weekly: Check error logs
- Monthly: Review analytics
- Quarterly: Update dependencies
- As needed: Update agent name/config

---

## Troubleshooting Guide

### Common Issues and Solutions

#### Agent Not Connecting
```bash
# Verify agent is deployed
lk agent list

# Check credentials
echo $LIVEKIT_URL
echo $LIVEKIT_API_KEY

# Test token generation
curl -X POST http://localhost:3000/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{"room_config":{"agents":[{"agent_name":"pd-voice-trialist-2-agent"}]}}'
```

#### Audio Issues
- Check browser permissions
- Verify microphone is not muted
- Test with different browser
- Check network latency

#### Deployment Fails
- Verify all environment variables set
- Check build logs for errors
- Ensure Node version matches

---

## Quick Commands Reference

```bash
# Development
npm run dev              # Start dev server
npm run build           # Build for production
npm run start           # Start production server

# LiveKit CLI
lk cloud auth           # Authenticate
lk agent list          # List deployed agents
lk app env             # Get environment variables

# Deployment
vercel                 # Deploy to Vercel
vercel --prod         # Deploy to production

# Testing
npm run test          # Run tests
npm run lint          # Check code quality
```

---

## Success Criteria

Your implementation is successful when:
- [x] Users can start voice conversations with one click
- [x] Agent responds within 2 seconds
- [x] Visual feedback shows agent state
- [x] Sessions last 15+ minutes without issues
- [x] Error rate is <1%
- [x] Works on all major browsers
- [x] Deployed to production URL

---

## Next Steps

After successful deployment:
1. Add analytics tracking
2. Implement transcript display
3. Add screen sharing capability
4. Create mobile app versions
5. Add multi-language support

---

## Support Resources

- LiveKit Documentation: https://docs.livekit.io
- LiveKit Discord: https://livekit.io/discord
- GitHub Issues: https://github.com/livekit-examples/agent-starter-react
- Internal Slack: #pandadoc-voice-agent

---

## Estimated Timeline

- **Day 1**: Phases 1-3 (Setup, Configuration, Integration)
- **Day 2**: Phases 4-5 (UI Enhancements, Testing)
- **Day 3**: Phases 6-7 (Deployment, Monitoring)

Total time: **2-3 days** for full implementation
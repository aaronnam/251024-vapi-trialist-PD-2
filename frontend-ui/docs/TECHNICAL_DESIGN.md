# Frontend UI Technical Design Document
## PandaDoc Voice Agent Web Interface

### Executive Summary
This document outlines the technical design for integrating a web frontend with the existing PandaDoc trial success voice agent deployed on LiveKit Cloud. The solution leverages LiveKit's agent-starter-react template to provide a production-ready interface with minimal custom development.

### Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   Web Browser   │────────▶│  Next.js App     │────────▶│ LiveKit Cloud   │
│                 │         │                  │         │                 │
│  React UI with  │◀────────│  - Token Server  │◀────────│  Voice Agent    │
│  Voice Controls │  WebRTC │  - API Routes    │  WebRTC │  (Deployed)     │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

### Key Design Decisions

#### 1. **Use Existing Template, Don't Reinvent**
- Leverage agent-starter-react for proven patterns
- Maintain compatibility with LiveKit SDK updates
- Reduce development time from weeks to days

#### 2. **Minimal Backend Modifications**
- No changes needed to deployed agent code
- Token server handles authentication and room creation
- Agent dispatch occurs automatically on room join

#### 3. **Configuration-Driven Customization**
- All branding via `app-config.ts`
- Environment variables for credentials
- No deep framework modifications

### Component Architecture

#### Frontend Components
```
frontend-ui/
├── app/
│   ├── (app)/                    # Main application routes
│   │   └── page.tsx              # Voice agent interface
│   ├── api/
│   │   └── connection-details/   # Token generation endpoint
│   │       └── route.ts          # JWT token creation
│   ├── ui/                       # Reusable components
│   │   ├── VoiceVisualizer.tsx  # Audio waveform display
│   │   ├── ConnectionStatus.tsx # Agent state indicator
│   │   └── CallControls.tsx     # Mute/end call buttons
│   └── lib/
│       └── livekit.ts           # SDK initialization
├── app-config.ts                 # Branding and features
└── .env.local                    # LiveKit credentials
```

#### Connection Flow
1. **User Loads Page** → React app initializes
2. **Click "Start Call"** → Request token from `/api/connection-details`
3. **Token Generated** → Includes room name and agent configuration
4. **WebRTC Connection** → User joins room via LiveKit SDK
5. **Agent Dispatched** → LiveKit Cloud spawns agent process
6. **Voice Pipeline Active** → Bidirectional audio streaming begins

### Security Architecture

#### Authentication Flow
```typescript
// Simplified token generation
const token = new AccessToken(
  process.env.LIVEKIT_API_KEY,
  process.env.LIVEKIT_API_SECRET,
  {
    identity: userId,
    ttl: '15m',
    roomJoin: true,
    room: roomName,
    canPublish: true,
    canSubscribe: true
  }
);
```

#### Security Considerations
- **Token Expiry**: 15-minute TTL prevents session hijacking
- **HTTPS Only**: Enforced in production deployment
- **Environment Isolation**: Credentials never exposed to client
- **Rate Limiting**: Implement on token endpoint (not in template)

### State Management

#### Agent State Tracking
The frontend tracks four primary states:
- `initializing` - Agent connecting to room
- `listening` - Ready for user input
- `thinking` - Processing user request
- `speaking` - Delivering response

```typescript
// State synchronization via LiveKit participant attributes
const agentState = participant.attributes['lk.agent.state'];
```

#### UI State Updates
- **Visual Feedback**: Bar visualizer changes with state
- **Audio Indicators**: Different patterns for listening/thinking
- **Connection Status**: Real-time disconnection handling

### Performance Optimizations

#### Connection Speed
- **Parallel Operations**: Token generation + room creation simultaneously
- **Agent Pre-warming**: Deploy agent on room creation, not user join
- **CDN Assets**: Static files served from edge locations

#### Audio Quality
- **Noise Cancellation**: LiveKit BVC enabled by default
- **Echo Suppression**: Built into WebRTC pipeline
- **Adaptive Bitrate**: Automatic quality adjustment

### Deployment Architecture

#### Infrastructure Requirements
```
Production Setup:
├── Vercel/Netlify           # Next.js hosting
├── LiveKit Cloud            # Agent runtime
└── Environment Variables    # API credentials
```

#### Scaling Considerations
- **Frontend**: Stateless, horizontally scalable
- **Token Server**: Lightweight, minimal CPU usage
- **Agent Instances**: Managed by LiveKit Cloud
- **WebRTC**: Direct peer connections, no proxy needed

### Error Handling Strategy

#### Connection Failures
```typescript
// Automatic reconnection with exponential backoff
const reconnectStrategy = {
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 5000,
  backoffFactor: 2
};
```

#### Agent Failures
- Display user-friendly error messages
- Provide manual retry option
- Log errors to monitoring service

### Monitoring & Analytics

#### Key Metrics
- **Connection Time**: Token request → agent speaking
- **Audio Quality**: Packet loss, jitter, latency
- **Session Duration**: Average call length
- **Error Rate**: Failed connections, disconnections

#### Integration Points
- LiveKit Cloud dashboard for agent metrics
- Frontend analytics (Google Analytics, Amplitude)
- Custom events for business metrics

### Future Enhancements

#### Phase 1 (Current)
- Basic voice interface
- Connection to deployed agent
- Visual feedback

#### Phase 2 (Optional)
- Transcript display
- Screen sharing capability
- File upload support

#### Phase 3 (Future)
- Virtual avatar integration
- Multi-language support
- Mobile app versions

### Technical Constraints

#### Browser Requirements
- **Minimum**: Chrome 88+, Firefox 78+, Safari 14+
- **Required APIs**: WebRTC, Web Audio, MediaStream

#### Network Requirements
- **Bandwidth**: 128kbps minimum for audio
- **Latency**: <150ms for optimal experience
- **Protocols**: WebSocket, SRTP, STUN/TURN

### Development Guidelines

#### Code Style
- TypeScript strict mode enabled
- ESLint with Next.js config
- Prettier for formatting

#### Testing Strategy
- Unit tests for utility functions
- Integration tests for API endpoints
- E2E tests for critical user flows

#### Deployment Process
1. Push to GitHub
2. Automatic deployment via Vercel
3. Environment variables set in dashboard
4. DNS configuration for custom domain

### Conclusion
This design provides a robust, scalable frontend for the PandaDoc voice agent while maintaining simplicity and leveraging proven patterns. The solution can be implemented in 2-3 days and requires minimal ongoing maintenance.
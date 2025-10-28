# PandaDoc Voice Agent Frontend UI

A web-based frontend interface for the PandaDoc trial success voice agent, built using LiveKit's agent-starter-react template.

## Overview

This frontend provides a clean, branded web interface for users to interact with the PandaDoc voice agent deployed on LiveKit Cloud. The solution leverages proven patterns from LiveKit's starter template while adding PandaDoc-specific branding and configuration.

## Architecture

```
User Browser ←→ Next.js App ←→ LiveKit Cloud ←→ Voice Agent
    (WebRTC)     (Token Server)    (WebSocket)    (Python)
```

## Quick Start

### Automated Setup (Recommended)
```bash
cd frontend-ui
./scripts/setup.sh
```

This will:
- Clone the agent-starter-react template
- Install dependencies
- Copy configuration templates
- Set up LiveKit credentials (if CLI available)
- Create helper scripts

### Manual Setup
```bash
# 1. Clone the template
git clone https://github.com/livekit-examples/agent-starter-react.git pandadoc-voice-ui
cd pandadoc-voice-ui

# 2. Install dependencies
npm install

# 3. Copy configuration
cp ../frontend-ui/config/app-config.template.ts app-config.ts
cp ../frontend-ui/config/.env.template .env.local

# 4. Configure LiveKit credentials
# Edit .env.local with your LiveKit Cloud credentials

# 5. Start development server
npm run dev
```

## Configuration

### Environment Variables (.env.local)
```env
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=APIxxxxxxxx
LIVEKIT_API_SECRET=xxxxxxxxxx
AGENT_NAME=pd-voice-trialist-2-agent
```

### App Configuration (app-config.ts)
- Company branding (name, logo, colors)
- Agent settings (name, display text)
- Feature toggles (chat, video, screen share)
- UI text customization

See `config/app-config.template.ts` for full configuration options.

### Branding & Design

The UI follows PandaDoc's official brand guidelines:
- **Colors**: Emerald Primary (#24856F) as the main accent color
- **Typography**: Graphik LC Alt Web (requires license from Brand Studio)
- **Design System**: See `docs/DESIGN_GUIDELINES.md` for complete specifications

**Important**: Graphik LC Alt Web font requires a license. Request permission from Brand Studio for download or use web-safe fallbacks (system fonts) during development.

## Project Structure

```
frontend-ui/
├── docs/
│   ├── TECHNICAL_DESIGN.md      # Architecture and design decisions
│   ├── IMPLEMENTATION_PLAN.md   # Step-by-step implementation guide
│   ├── DESIGN_GUIDELINES.md     # PandaDoc brand colors and typography
│   └── LOGO_USAGE_GUIDE.md      # Logo variants and usage recommendations
├── config/
│   ├── app-config.template.ts   # Application configuration template
│   └── .env.template            # Environment variables template
├── scripts/
│   └── setup.sh                 # Automated setup script
├── logos/                       # PandaDoc logo assets
│   ├── Emerald_black_pd_brandmark.png           # Full logo (light backgrounds)
│   ├── Emerald_white_pd_symbol_brandmark.png    # Symbol only (icons/favicons)
│   └── panda-logo-2.png                         # Mascot (friendly contexts)
└── README.md                    # This file

pandadoc-voice-ui/               # Created by setup script
├── app/
│   ├── (app)/                   # Main application routes
│   ├── api/
│   │   └── connection-details/  # Token generation endpoint
│   └── ui/                      # UI components
├── public/                      # Static assets
├── app-config.ts               # Your configuration
└── .env.local                  # Your credentials
```

## Key Features

### Implemented
- ✅ One-click voice connection
- ✅ Real-time audio streaming
- ✅ Visual voice activity indicator
- ✅ Connection status display
- ✅ PandaDoc branding

### Planned Enhancements
- 📝 Transcript display
- 🖥️ Screen sharing capability
- 📁 File upload support
- 🌍 Multi-language support
- 📱 Mobile app versions

## Development

### Available Scripts
```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run start    # Start production server
npm run lint     # Run linting
npm run format   # Format code
```

### Testing the Agent Connection
1. Ensure your agent is deployed to LiveKit Cloud
2. Verify credentials in `.env.local`
3. Start the development server
4. Click "Start Trial Assistance"
5. Allow microphone access
6. Speak to test the connection

## Deployment

### Deploy to Vercel (Recommended)
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Deploy to production
vercel --prod
```

### Environment Variables in Production
Set these in your Vercel dashboard:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`

### Custom Domain
1. Go to Vercel Dashboard > Settings > Domains
2. Add your domain (e.g., voice.pandadoc.com)
3. Update DNS records as instructed

## Troubleshooting

### Agent Not Connecting
```bash
# Verify agent is deployed
lk agent list

# Check credentials
echo $LIVEKIT_URL

# Test token generation
curl -X POST http://localhost:3000/api/connection-details \
  -H "Content-Type: application/json" \
  -d '{"room_config":{"agents":[{"agent_name":"pd-voice-trialist-2-agent"}]}}'
```

### Audio Issues
- Check browser microphone permissions
- Verify microphone is not muted
- Test with a different browser
- Check network latency

### Build Errors
- Ensure Node.js 18+ is installed
- Clear node_modules and reinstall
- Check for TypeScript errors

## Monitoring

### Key Metrics to Track
- Connection time (target: <2s)
- Audio quality (packet loss, jitter)
- Session duration
- Error rate (target: <1%)

### Recommended Tools
- LiveKit Cloud Dashboard (agent metrics)
- Vercel Analytics (web vitals)
- Amplitude (user behavior)
- Sentry (error tracking)

## Security Considerations

- JWT tokens expire after 15-30 minutes
- API credentials never exposed to client
- All traffic over HTTPS/WSS
- Rate limiting on token endpoint recommended

## Browser Support

| Browser | Minimum Version |
|---------|----------------|
| Chrome  | 88+           |
| Firefox | 78+           |
| Safari  | 14+           |
| Edge    | 88+           |

## Resources

- [LiveKit Documentation](https://docs.livekit.io)
- [LiveKit Discord](https://livekit.io/discord)
- [Agent Starter React](https://github.com/livekit-examples/agent-starter-react)
- [Technical Design](./docs/TECHNICAL_DESIGN.md)
- [Implementation Plan](./docs/IMPLEMENTATION_PLAN.md)
- [Design Guidelines](./docs/DESIGN_GUIDELINES.md)
- [Logo Usage Guide](./docs/LOGO_USAGE_GUIDE.md)

## Support

For issues or questions:
- Check the [Troubleshooting](#troubleshooting) section
- Review the [Implementation Plan](./docs/IMPLEMENTATION_PLAN.md)
- Visit LiveKit Discord for community support
- Create an issue in this repository

## License

This frontend is based on LiveKit's agent-starter-react template (MIT License).
Custom code and configurations are proprietary to PandaDoc.

---

**Estimated Implementation Time**: 2-3 days

**Current Status**: Ready for implementation
# Infrastructure & Data Storage Questions - Answered

## Frontend Repository Location

The frontend is located at **https://github.com/aaronnam/251024-vapi-trialist-PD-2** (this repo). We don't currently have a separate frontend repository—the voice agent backend is the main focus here.

For production deployment, you'd typically use one of LiveKit's frontend starters:
- **Web**: React/Next.js
- **iOS/macOS**: Swift
- **Flutter**: Cross-platform
- **React Native**: Mobile
- **Android**: Kotlin/Jetpack Compose
- **Web Embed**: Embeddable widget

---

## LiveKit Contract & Legal Data Processing

✅ **Contract Status**: We don't have a separate contract with LiveKit beyond the standard LiveKit Cloud terms of service you agree to when signing up.

✅ **Data Processing Coverage**: LiveKit's Data Processing Addendum (DPA) covers all data processed through their platform.

**Key Points from LiveKit's DPA:**
- LiveKit acts as a **data processor** for customer content
- Analytics data is retained (encrypted) for **maximum 14 days**
- LiveKit may retain data if required by law while maintaining encryption
- You have full control over who can access your data through API keys and authentication

---

## Session Transcript Storage - Confirmed

**Session transcripts are saved exclusively in our AWS S3 bucket**, NOT on LiveKit's side.

**How it works:**
- Agent captures full transcripts via `my-app/src/utils/analytics_queue.py` (lines 78-125)
- Data compressed with gzip (~80% savings) and uploaded to S3 with date partitioning
- S3 bucket: `pandadoc-voice-analytics-1761683081/sessions/year=2025/month=10/day=31/`
- LiveKit only handles realtime media transport; logs retained 14 days max (encrypted)

**Data Retention & Security:**
- Location: AWS S3 (us-west-1)
- Retention: Indefinite (until deleted)
- Contents: Full transcript, user metadata, qualification signals, tool calls, cost breakdown
- Access: Restricted to AWS credentials
- Pipeline: Agent → CloudWatch Logs → S3

---

## Self-Hosting LiveKit on AWS - Feasibility Analysis

### ✅ Yes, It's Feasible - But With Caveats

LiveKit is **fully self-hostable on AWS**. The architecture is identical to LiveKit Cloud, so migration is theoretically seamless (just change the connection URL).

### Infrastructure You'd Need

#### Compute & Orchestration
- **EKS** (Elastic Kubernetes Service) or **EC2** instances
- **Host networking required** (one LiveKit pod per node)
- **Compute-optimized instance types** (C5, C6, C7 families)
- **Port requirements**: UDP/TCP range 50000-60000, port 7880-7881

#### Networking & Load Balancing
- **ALB (Application Load Balancer)** for WebSocket signal connections
- **Layer 4 Load Balancer** for TURN/TLS traffic (UDP port 443 or 5349)
- **Network**: 10Gbps+ ethernet minimum recommended
- **SSL Certificates**: One for main domain (wss://livekit.yourhost.com), one for TURN

#### Storage & Databases
- **Redis** instance for distributed room state and routing
- **S3** for recordings/egress (same as today)
- **CloudWatch** for logging and monitoring

### What You'd LOSE vs LiveKit Cloud

| Feature | LiveKit Cloud | Self-Hosted |
|---------|---------------|------------|
| **Model Inference** | Hosted (OpenAI, Deepgram, Cartesia, etc.) | Direct API keys required |
| **Noise Cancellation** | BVC (enhanced) included | Need alternative solution |
| **Agent Deployment** | Built-in, auto-scaling | Manage your own Docker/K8s |
| **Global Edge Network** | Automatic low-latency routing | Single region only |
| **Operational Overhead** | Zero | Full responsibility |
| **SSL Management** | Automatic | Manual renewal required |
| **Monitoring/Alerts** | Included dashboard | Build your own stack |
| **Support** | Premium available | Community/DIY |

### What You'd KEEP

- ✅ Same SDKs and APIs (code portability)
- ✅ WebRTC media transport
- ✅ Realtime collaboration features
- ✅ Full data control and residency
- ✅ Open-source flexibility

### Cost Considerations

**LiveKit Cloud** (Current):
- Pay-as-you-go based on usage
- Fixed operational overhead (we pay them)
- At current volume: ~$50-500/month for compute + bandwidth

**Self-Hosted AWS**:
- **EKS Cluster**: $73/month + node costs
- **EC2 Instances**: $200-1000+/month depending on scale
- **Redis**: $50-500+/month depending on setup
- **Data Transfer**: Same as now (~$0.02/GB out)
- **Operational Time**: 10-20 hours/month for maintenance
  - K8s management
  - SSL certificate renewals
  - Monitoring and alerting
  - Scaling decisions

**At our current scale**: Self-hosting would likely **cost MORE** when you factor in operational overhead.

### Migration Path (If Needed)

1. Deploy LiveKit to AWS (Helm charts available)
2. Set up Redis, load balancers, SSL certificates
3. Update `LIVEKIT_URL` in `my-app/src/agent.py`
4. Switch to direct API credentials for AI models (remove LiveKit Cloud inference)
5. Remove enhanced noise cancellation plugin
6. Test thoroughly in console mode
7. Gradual traffic migration

### Recommendation

**Stick with LiveKit Cloud** unless you have:
- Specific compliance requirements (data residency, on-premises only)
- Very high scale that makes ops time worthwhile
- Need for extreme customization
- Regulatory requirements (HIPAA, FedRAMP, etc.)

**Why?**
- We're already storing all sensitive data (transcripts) in our own S3
- Operational complexity not justified at current scale
- Easy to switch if requirements change (cloud-agnostic APIs)
- Focus engineering time on product, not infrastructure

---

## Quick Reference

| Question | Answer |
|----------|--------|
| **Frontend repo?** | This repo (GitHub: aaronnam/251024-vapi-trialist-PD-2) |
| **LiveKit contract?** | No separate contract (standard ToS only) |
| **Transcripts on LiveKit?** | No - all in our AWS S3 bucket |
| **Transcripts location?** | S3: pandadoc-voice-analytics-1761683081/sessions/ |
| **LiveKit data retention?** | Analytics only, 14 days max (encrypted) |
| **Self-host feasible?** | Yes, but ops overhead likely not worth it at current scale |
| **Need contract for data processing?** | LiveKit's DPA covers it |

---

**Last Updated**: October 31, 2025
**Research Depth**: Verified against LiveKit docs, AWS infrastructure, codebase analysis

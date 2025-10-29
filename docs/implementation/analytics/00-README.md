# Analytics System Documentation

**Quick Start**: Looking to understand or debug the analytics system? Start with [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - it's the complete, authoritative guide.

## 📚 Documentation Structure

```
analytics/
├── 00-README.md                           ← You are here
├── 01-DEPLOYMENT_REFERENCE.md             ← ⭐ START HERE - Complete reference
│
├── architecture/                          → How it works
│   ├── strategy.md                        → Overall design principles
│   ├── data-flow-detailed.md              → Exhaustive data flow specification
│   └── data-flow-simplified.md            → Simplified for diagrams/presentations
│
├── guides/                                → Step-by-step setup instructions
│   ├── cloudwatch-setup.md                → CloudWatch deployment guide
│   ├── s3-export-setup.md                 → S3 export configuration
│   └── livekit-cloud-storage.md           → LiveKit Cloud storage strategy
│
└── project-history/                       → Implementation timeline
    ├── implementation-plan.md             → Original phased plan
    └── phase-1-completion.md              → Phase 1 completion report
```

---

## 🎯 Quick Navigation

### New to the Analytics System?
1. **Read**: [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md)
   - Complete architecture overview
   - All components explained
   - Configuration details
2. **Understand**: [`architecture/strategy.md`](./architecture/strategy.md)
   - Design principles
   - Why we built it this way
3. **Explore**: [`architecture/data-flow-detailed.md`](./architecture/data-flow-detailed.md)
   - Detailed data flow through all layers

### Deploying or Configuring?
1. **Main Guide**: [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) (Deployment section)
2. **CloudWatch**: [`guides/cloudwatch-setup.md`](./guides/cloudwatch-setup.md)
3. **S3 Export**: [`guides/s3-export-setup.md`](./guides/s3-export-setup.md)

### Debugging Issues?
1. **Troubleshooting**: [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) (Monitoring & Debugging section)
   - Common issues with solutions
   - Health check procedures
   - Diagnostic commands

### Understanding the Architecture?
1. **High-level**: [`architecture/strategy.md`](./architecture/strategy.md)
2. **Detailed**: [`architecture/data-flow-detailed.md`](./architecture/data-flow-detailed.md)
3. **Visual**: [`architecture/data-flow-simplified.md`](./architecture/data-flow-simplified.md)

### Historical Context?
1. **Planning**: [`project-history/implementation-plan.md`](./project-history/implementation-plan.md)
2. **Completion**: [`project-history/phase-1-completion.md`](./project-history/phase-1-completion.md)

---

## 📖 Document Descriptions

### Primary Reference

#### [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md)
**The authoritative, complete guide to the analytics system.**

This is the single most important document - it contains everything you need:
- **Architecture**: Complete system overview with diagrams
- **Data Flow**: Step-by-step explanation of how data moves through the system
- **Components**: Deep dive into each component (agent, analytics_queue, CloudWatch, Firehose, S3)
- **Configuration**: All environment variables, IAM policies, settings
- **Deployment**: Complete deployment procedures with verification
- **Monitoring & Debugging**: Troubleshooting guide with solutions for common issues
- **Cost Analysis**: Detailed cost breakdown with optimization tips
- **Future Enhancements**: Planned Phase 2/3 features

**Use this when**: You need to understand, deploy, configure, or debug the analytics system.

---

### Architecture Documents

#### [`architecture/strategy.md`](./architecture/strategy.md)
**Overall analytics strategy and design philosophy.**

Contents:
- Problem statement and business context
- Separated architecture pattern (collection vs. analysis)
- Design principles (zero latency, LiveKit native, cost-optimized)
- Component overview
- Data types collected
- Analytics pipeline phases
- Use cases and queries

**Use this when**: You want to understand *why* the system is designed this way, or need to explain the approach to stakeholders.

#### [`architecture/data-flow-detailed.md`](./architecture/data-flow-detailed.md)
**Exhaustive, technical data flow specification.**

Contents:
- Complete data flow from collection → CloudWatch → Firehose → S3
- Every field tracked and its purpose
- Data transformations at each stage
- Timing and performance characteristics
- Tool-specific data structures
- LiveKit metrics details

**Use this when**: You need detailed technical specs, writing integration code, or debugging data issues.

#### [`architecture/data-flow-simplified.md`](./architecture/data-flow-simplified.md)
**High-level data flow for presentations and diagrams.**

Contents:
- Simplified bullet-point format
- Easy to copy into Figma, PowerPoint, or diagrams
- No technical jargon
- Focus on key concepts

**Use this when**: Creating presentations, explaining to non-technical stakeholders, or making diagrams.

---

### Setup Guides

#### [`guides/cloudwatch-setup.md`](./guides/cloudwatch-setup.md)
**Step-by-step guide to set up CloudWatch logging.**

Contents:
- CloudWatch Logs configuration
- IAM user creation
- AWS credentials setup
- LiveKit Cloud integration
- CloudWatch Insights queries
- Testing and verification

**Use this when**: Setting up CloudWatch for the first time, or troubleshooting CloudWatch integration.

#### [`guides/s3-export-setup.md`](./guides/s3-export-setup.md)
**Complete guide to exporting analytics to S3.**

Contents:
- Three approaches to S3 export (Firehose, Lambda, Direct)
- Kinesis Firehose setup (recommended)
- S3 bucket configuration
- CloudWatch subscription filters
- Athena query setup
- Cost optimization

**Use this when**: Setting up S3 export, configuring Firehose, or enabling Athena queries.

#### [`guides/livekit-cloud-storage.md`](./guides/livekit-cloud-storage.md)
**Strategy for storing analytics data in LiveKit Cloud deployments.**

Contents:
- LiveKit Cloud log forwarding
- Structured logging approach
- CloudWatch integration
- Why CloudWatch is the most elegant solution
- Migration path to advanced analytics

**Use this when**: Understanding why we chose CloudWatch, or planning LiveKit Cloud deployments.

---

### Project History

#### [`project-history/implementation-plan.md`](./project-history/implementation-plan.md)
**Original phased implementation plan.**

Contents:
- Phase 1: Lightweight collection (completed)
- Phase 2: Analytics pipeline (planned)
- Phase 3: AI insights (planned)
- Technical requirements for each phase
- LiveKit compliance checks

**Use this when**: Understanding the project roadmap, planning Phase 2/3, or reviewing original requirements.

#### [`project-history/phase-1-completion.md`](./project-history/phase-1-completion.md)
**Completion report for Phase 1 implementation.**

Contents:
- Summary of changes made
- Files created/modified
- Code statistics
- Performance impact analysis
- Testing results
- What data is collected
- LiveKit standards compliance
- Next steps (Phase 2)

**Use this when**: Understanding what was implemented in Phase 1, or verifying the implementation is complete.

---

## 🔍 Common Search Scenarios

### "How do I query analytics data?"
→ [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "CloudWatch Insights Queries" or "Athena"

### "Analytics events aren't appearing in CloudWatch"
→ [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "No analytics events in CloudWatch"

### "How much does this cost?"
→ [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "Cost Analysis"

### "How do I deploy changes?"
→ [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "Deployment Steps"

### "What signals are being detected?"
→ [`architecture/data-flow-detailed.md`](./architecture/data-flow-detailed.md) - Search for "Signal Discovery"

### "How do I set up S3 export?"
→ [`guides/s3-export-setup.md`](./guides/s3-export-setup.md) - Start from the beginning

### "Why isn't data appearing in S3?"
→ [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "Analytics events in CloudWatch but not in S3"

### "What's the architecture overview?"
→ [`architecture/strategy.md`](./architecture/strategy.md) or [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Both have architecture sections

### "How do I add AWS credentials?"
→ [`guides/cloudwatch-setup.md`](./guides/cloudwatch-setup.md) or [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - Search for "AWS credentials"

---

## 📊 System Overview (Quick Reference)

### Architecture
```
Voice Agent → Structured Logs → CloudWatch → Firehose → S3
```

### Key Components
- **Agent**: Collects data (0ms latency impact)
- **analytics_queue.py**: Structured JSON logging
- **CloudWatch**: Real-time log ingestion and queries
- **Kinesis Firehose**: Automatic streaming to S3
- **S3**: Long-term storage with date partitioning

### Key Files in Codebase
- `my-app/src/agent.py` - Agent with analytics collection
- `my-app/src/utils/analytics_queue.py` - Structured logging utility

### Key Infrastructure
- **S3 Bucket**: `pandadoc-voice-analytics-1761683081`
- **Firehose Stream**: `voice-analytics-to-s3`
- **Agent ID**: `CA_9b4oemVRtDEm`
- **Region**: us-west-1

### Key Commands
```bash
# Deploy agent
lk agent deploy

# Check status
lk agent status

# View logs
lk agent logs --tail

# Check CloudWatch
aws logs tail /aws/livekit/pd-voice-trialist-4 \
  --filter-pattern '{ $._event_type = "session_analytics" }' \
  --region us-west-1

# Check S3
aws s3 ls s3://pandadoc-voice-analytics-1761683081/sessions/ \
  --recursive --region us-west-1
```

---

## 🚀 Getting Started Checklist

### First Time Setup
- [ ] Read [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) (Architecture + Configuration sections)
- [ ] Verify AWS credentials are configured (`lk agent secrets`)
- [ ] Check agent is deployed and running (`lk agent status`)
- [ ] Verify CloudWatch log group exists
- [ ] Run test session and confirm analytics export
- [ ] Check CloudWatch Insights for analytics events
- [ ] (Optional) Set up S3 export via Firehose

### Troubleshooting
- [ ] Check agent logs (`lk agent logs --tail`)
- [ ] Check CloudWatch for analytics events
- [ ] Verify subscription filter is active (if using S3)
- [ ] Check Firehose metrics (if using S3)
- [ ] Review troubleshooting section in deployment reference

### Development
- [ ] Understand architecture ([`architecture/strategy.md`](./architecture/strategy.md))
- [ ] Review data flow ([`architecture/data-flow-detailed.md`](./architecture/data-flow-detailed.md))
- [ ] Check Phase 2/3 plans ([`project-history/implementation-plan.md`](./project-history/implementation-plan.md))

---

## 📝 Document Maintenance

### When to Update

**Update [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) when**:
- Architecture changes
- New components added
- Configuration changes
- Common issues discovered
- Cost structure changes

**Update architecture docs when**:
- Design principles change
- New data types collected
- Pipeline stages modified

**Update guides when**:
- Setup procedures change
- New tools/services added
- Troubleshooting steps updated

**Add to project-history when**:
- Major phases completed
- Significant milestones reached
- Architecture decisions documented

### Document Ownership
- **Maintainer**: Platform Team
- **Last Major Update**: 2025-01-28
- **Review Frequency**: Quarterly or after major changes

---

## 🤝 Contributing

When adding new documentation:
1. Add to appropriate folder based on purpose
2. Update this README with link and description
3. Update [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) if relevant
4. Use clear, searchable titles
5. Include examples and code snippets

---

**Need help?** Start with [`01-DEPLOYMENT_REFERENCE.md`](./01-DEPLOYMENT_REFERENCE.md) - it has everything!
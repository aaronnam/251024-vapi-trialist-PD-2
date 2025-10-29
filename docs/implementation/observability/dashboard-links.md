# Voice Agent Performance Dashboard - Quick Links

**Last Updated**: 2025-10-29
**Status**: ✅ Live and Monitoring

---

## Main Dashboard
**[Open CloudWatch Dashboard](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance)**

This dashboard displays:
- P95 Latency (5-minute rolling window)
- Error Rate (1-minute granularity)
- Latency Breakdown (EOU, LLM, TTS components)
- Qualified Leads (24-hour rolling)
- Recent Errors (last 10)
- Slow Sessions (>2s latency)

---

## CloudWatch Insights Saved Queries

Access these pre-built queries in [CloudWatch Logs Insights](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#logsV2:logs-insights):

1. **Voice Agent - P95 Latency** - Percentile latency breakdown (P95, P99, avg)
2. **Voice Agent - Error Rate** - Error count by minute
3. **Voice Agent - Latency Breakdown** - Component-level latency (EOU, LLM, TTS)
4. **Voice Agent - Qualified Leads** - Leads meeting qualification criteria
5. **Voice Agent - Recent Errors** - Last 10 errors with session IDs
6. **Voice Agent - Slow Sessions** - Sessions exceeding 2s latency
7. **Voice Agent - Tool Success Rate** - Tool execution success metrics
8. **Voice Agent - Token Usage** - Hourly LLM token consumption

---

## Tracing & Debugging

**[Langfuse Traces](https://us.cloud.langfuse.com)** - View distributed traces for individual sessions
- Session-level filtering by `langfuse.session.id`
- Full request timeline with component timings
- Tool execution details

**[LiveKit Cloud Agent](https://cloud.livekit.io/projects/pd-voice-trialist-4/agents)** - Agent status and deployment logs

---

## CloudWatch Alarms

**[View All Alarms](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#alarmsV2:)**

Active alarms:
- **VoiceAgent-HighLatency** - Triggers when >5 high-latency events in 5 minutes
- **VoiceAgent-HighErrorRate** - Triggers when >10 errors in 5 minutes (2 consecutive periods)
- **VoiceAgent-NoMetrics** - Triggers when no metrics received for 5 minutes (agent down)

**Notifications**: Sent to SNS topic `voice-agent-alerts`

---

## Log Groups

**[Live Logs](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#logsV2:log-groups/log-group/CA_9b4oemVRtDEm)**

Log group: `CA_9b4oemVRtDEm`

Event types to filter:
- `_event_type = "voice_metrics"` - Performance metrics
- `_event_type = "session_analytics"` - Session summaries
- `@message like /ERROR/` - Error logs

---

## Daily Monitoring Workflow

1. **Start of day**: Check [main dashboard](https://us-west-1.console.aws.amazon.com/cloudwatch/home?region=us-west-1#dashboards:name=pd-voice-agent-performance)
   - Verify P95 latency < 1.5s
   - Check error rate < 1%
   - Review qualified leads from yesterday

2. **During day**: Watch for SNS alerts on `voice-agent-alerts`
   - High latency alert → Check Langfuse traces for bottleneck
   - High error rate → Check recent errors query for patterns
   - No metrics alert → Check agent status on LiveKit Cloud

3. **End of day**: Run qualified leads query for tomorrow's follow-up

---

## Cost & Resource Info

| Component | Status | Region |
|-----------|--------|--------|
| CloudWatch Dashboard | ✅ Active | us-west-1 |
| CloudWatch Logs Queries | ✅ Saved | us-west-1 |
| CloudWatch Alarms | ✅ Active | us-west-1 |
| SNS Topic | ✅ Active | us-west-1 |
| Agent Log Group | ✅ Active | us-west-1 |

**Monthly cost**: ~$8.30 (dashboard + queries + alarms)

---

## Implementation Details

| Component | Status |
|-----------|--------|
| Dashboard template | ✅ Created at `docs/implementation/observability/dashboard-template.json` |
| Query definitions | ✅ 8 saved queries in CloudWatch Logs |
| Metric filters | ✅ 2 filters (HighLatency, Error) |
| Alarms | ✅ 3 alarms with SNS integration |
| SNS notifications | ✅ Topic: `voice-agent-alerts` |

---

## Troubleshooting

**Dashboard not showing data?**
- Check log group `CA_9b4oemVRtDEm` has recent entries
- Verify agent is running on LiveKit Cloud
- Check that metrics are being logged with `_event_type = "voice_metrics"`

**Alarms not triggering?**
- Verify SNS topic subscription is confirmed
- Check alarm state: `aws cloudwatch describe-alarms --alarm-name-prefix "VoiceAgent-"`
- Review metric filter patterns for false negatives

**Need to adjust thresholds?**
- P95 latency threshold: Edit `VoiceAgent-HighLatency` alarm
- Error threshold: Edit `VoiceAgent-HighErrorRate` alarm
- All adjustments via CloudWatch console or `aws cloudwatch put-metric-alarm`

---

## Next Steps

1. **Test the dashboard** - View in browser and verify all widgets load
2. **Subscribe to SNS** - Confirm email subscription to `voice-agent-alerts`
3. **Review thresholds** - Adjust P95 latency and error thresholds based on baseline
4. **Daily check** - Add dashboard to morning monitoring routine

---

**Questions?** Check `docs/implementation/observability/PERFORMANCE_DASHBOARD_SPEC.md` for full implementation guide.

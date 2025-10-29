# Email to Salesforce Admin

---

**To**: [Salesforce Admin Name]
**From**: Aaron Nam (Voice AI Engineering)
**Subject**: Voice Agent Call Tracking - Need SF Integration User
**Date**: 2025-10-29

---

Hi [Name],

We've launched a voice AI agent for trial success and need to log call activity in Salesforce so sales teams can see trial engagement.

## What We're Building

Daily script that reads voice call data from S3 and creates Salesforce Tasks:

- **Creates**: One Task per voice call (linked to Contact/Lead via email)
- **Contains**: Call duration, discovered use case, pain points, actions taken (e.g., meeting booked)
- **Runs**: Daily at 2 AM (24-hour delay)
- **Uses**: Standard Task object (no custom fields needed)

## What We Need From You

1. **Salesforce integration user** with:
   - API access enabled
   - Read access to Contact and Lead objects
   - Create access to Task object

2. **Credentials** (securely shared):
   - Username
   - Password
   - Security token

That's it. No custom objects, no custom fields, no Apex code.

## Timeline

- **Day 1**: Set up script with your credentials
- **Day 2**: Deploy to production
- **Week 1**: Monitor and gather sales feedback
- **Week 2+**: Iterate based on what sales actually needs

## Sample Output

Sales teams will see Tasks like this on Contact records:

**Subject**: Voice AI Call - 2025-10-29
**Status**: Completed
**Duration**: 15 minutes
**Description**:
```
Voice AI Call Summary
Duration: 15 minutes

Discovered Information:
• Use Case: sales_proposals
• Team Size: 10-50
• Pain Points: manual contract creation, slow approval process

Agent Actions:
✓ Booked sales meeting for 2025-11-01
✓ Sent product documentation
```

## Why This Approach

Starting simple:
- Zero infrastructure costs
- No Salesforce customization
- 2 days to production
- Easy to upgrade later if needed

If sales wants real-time updates or custom fields, we'll add them based on their feedback.

## Next Steps

Reply with integration user credentials (or schedule 15-min call to discuss).

Detailed proposal attached: `SALESFORCE_INTEGRATION_SIMPLE.md`

Thanks,
Aaron

---

**Attachments**:
- SALESFORCE_INTEGRATION_SIMPLE.md (full technical spec)

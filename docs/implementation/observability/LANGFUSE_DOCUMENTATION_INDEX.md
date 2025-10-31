# Langfuse Documentation Index

Complete documentation collection for search, filtering, and observability with Langfuse in the PandaDoc Voice AI trial success agent.

## 📚 Documentation Files

### 1. **LANGFUSE_SEARCH_FILTERING_GUIDE.md** (Primary Reference)
**The comprehensive guide** - Start here for detailed information about all search and filtering capabilities.

**Contains:**
- How to search by session IDs (grouping related traces)
- How to filter by user IDs (tracking individual users)
- How to filter by metadata fields (custom JSON data)
- Full-text search for finding specific content
- Filtering by trace level and type
- Tag-based organization and filtering
- Error trace identification
- Tool call and function execution search
- Natural language filtering (beta feature)
- Time-range filtering
- Best practices for organizing traces
- Advanced programmatic analysis examples
- Debugging specific conversation issues
- Integration examples with your LiveKit agent

**Use when:** You need detailed explanations, code examples, or best practices for any search/filter feature.

---

### 2. **LANGFUSE_QUICK_REFERENCE.md** (Cheat Sheet)
**Fast lookup guide** - Bookmark this for quick command/syntax reference.

**Contains:**
- UI search tips (quick table)
- Python SDK quick snippets (copy-paste ready)
- Trace anatomy for searching (what's searchable)
- Metadata vs Tags comparison
- Common debugging workflows
- Observation type cheat sheet
- Filter operators reference
- Limits and gotchas
- Dashboard navigation
- Useful API endpoints

**Use when:** You need to quickly remember syntax or find a command.

---

### 3. **LANGFUSE_USER_ID_COMPLETE_SUMMARY.md** (Deep Dive)
**Specialized guide** - Comprehensive coverage of user ID filtering and user tracking.

**Contains:**
- User ID configuration across SDKs
- User profile and analytics
- User-based filtering patterns
- Cost tracking per user
- User session management
- User segmentation examples
- Integration patterns with LiveKit

**Use when:** You need comprehensive user tracking or user-based analysis.

---

### 4. **LANGFUSE_USER_ID_GUIDE.md** (Quick User ID Reference)
**Quick user ID guide** - Focused reference for user ID operations.

**Use when:** You just need user ID setup basics.

---

## 🎯 Quick Navigation by Task

### Finding Specific Conversations
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 1: "Filter by Session ID"

### Tracking Individual Users
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 2: "Filter by User ID"
or **LANGFUSE_USER_ID_COMPLETE_SUMMARY.md**

### Searching for Text Content
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 4: "Full-Text Search"

### Finding Errors/Debugging Issues
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 7: "Filter by Errors"

### Analyzing Tool Calls
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 8: "Filter by Observation Type (Tool Calls)"

### Cost Analysis
→ **LANGFUSE_QUICK_REFERENCE.md** → "Python SDK Quick Snippets" → "Get LLM generations"

### Common Debugging Scenarios
→ **LANGFUSE_QUICK_REFERENCE.md** → "Common Debugging Flows"

### Setting Up Traces for Easy Finding
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → "Integration with Your Agent"

### Metadata Filtering Strategy
→ **LANGFUSE_SEARCH_FILTERING_GUIDE.md** → Section 3: "Filter by Metadata Fields"

---

## 🔍 Feature Matrix

| Feature | Documentation | Complexity | Common? |
|---------|---|---|---|
| **Session ID filtering** | Guide (Sec 1) | Beginner | Very |
| **User ID filtering** | Guide (Sec 2) + User Summary | Beginner | Very |
| **Text search** | Guide (Sec 4) | Beginner | Very |
| **Tags** | Guide (Sec 6) | Beginner | Often |
| **Errors** | Guide (Sec 7) | Beginner | Very |
| **Metadata** | Guide (Sec 3) | Intermediate | Often |
| **Observations** | Guide (Sec 8) | Intermediate | Often |
| **Natural Language** | Guide (Sec 9) | Beginner | Emerging |
| **Metrics API** | Guide (Advanced section) | Advanced | Rarely |
| **Programmatic queries** | Guide (Advanced section) | Advanced | Rarely |

---

## 🚀 Getting Started Checklist

- [ ] Read: LANGFUSE_SEARCH_FILTERING_GUIDE.md - Sections 1-4 (basic searches)
- [ ] Bookmark: LANGFUSE_QUICK_REFERENCE.md (for quick syntax lookup)
- [ ] Setup: Add session_id and user_id to your traces
- [ ] Test: Use UI to filter by session_id and user_id
- [ ] Explore: View an error trace to understand trace structure
- [ ] Advanced: Read Sections 3 and 8 (metadata and observations)
- [ ] Integrate: Implement metadata/tags in your agent code

---

## 📖 Langfuse Official Resources

For the latest information, always check official sources:

- **Main Documentation**: https://langfuse.com/docs/
- **Query Traces**: https://langfuse.com/docs/query-traces
- **Sessions**: https://langfuse.com/docs/tracing-features/sessions
- **Users**: https://langfuse.com/docs/tracing-features/users
- **Tags**: https://langfuse.com/docs/tracing-features/tags
- **Metadata**: https://langfuse.com/docs/tracing-features/metadata
- **Observation Types**: https://langfuse.com/docs/observability/features/observation-types
- **Natural Language Filtering**: https://langfuse.com/changelog/2025-09-30-natural-language-filters

---

## 🔧 Integration Points

Your LiveKit agent code integrates with Langfuse through:

**Telemetry Setup:**
- File: `/my-app/src/utils/telemetry.py`
- Function: `setup_observability(metadata={...})`
- Handles: OpenTelemetry configuration and LangFuse connection

**Agent Code:**
- File: `/my-app/src/agent.py`
- Location: Entrypoint and turn handlers
- Adds: session_id, user_id, tags, metadata to traces

**Key Configuration:**
```python
# In your agent
trace_provider = setup_observability(
    metadata={
        "langfuse.session.id": room_name,
        "langfuse.user.id": user_id,
        "environment": "production",
        "agent_version": "1.0.0"
    }
)

# During execution
langfuse_context.update_current_trace(
    tags=["qualified", "consent-given"],
    metadata={"qualification_score": 8.5}
)
```

---

## 🎓 Learning Path

### Beginner (30 minutes)
1. Read: Guide Section 1 (Session ID filtering)
2. Read: Guide Section 2 (User ID filtering)
3. Practice: Filter some traces in Langfuse UI
4. Result: Can find specific conversations and users

### Intermediate (1 hour)
1. Read: Guide Sections 3-8 (metadata, tags, observations)
2. Read: Quick Reference (cheat sheets)
3. Practice: Use Python SDK to query traces programmatically
4. Result: Can filter by custom metadata, find tool calls

### Advanced (2+ hours)
1. Read: Guide Advanced sections (Metrics API)
2. Study: Integration patterns with your agent
3. Implement: Metadata strategy for your use case
4. Build: Custom analysis scripts
5. Result: Can perform complex queries and analysis

---

## 🐛 Troubleshooting Guide

### Problem: Can't find recent traces
**Solution:** 15-30s ingestion delay
- File: LANGFUSE_QUICK_REFERENCE.md → "Langfuse Limits & Gotchas"
- Or: LANGFUSE_SEARCH_FILTERING_GUIDE.md → "Troubleshooting"

### Problem: Metadata filtering isn't working
**Solution:** Check metadata was set early in trace
- File: LANGFUSE_SEARCH_FILTERING_GUIDE.md → "Troubleshooting Common Search Issues"

### Problem: Can't filter by tags
**Solution:** Avoid special characters in tags
- File: LANGFUSE_QUICK_REFERENCE.md → "Langfuse Limits & Gotchas"
- Or: LANGFUSE_SEARCH_FILTERING_GUIDE.md → "Troubleshooting"

### Problem: User traces not grouping
**Solution:** Set user_id and session_id together
- File: LANGFUSE_USER_ID_COMPLETE_SUMMARY.md
- Or: LANGFUSE_SEARCH_FILTERING_GUIDE.md → Section 2

---

## 📊 Reference Tables

### Filter Methods Comparison
| Method | Speed | Complexity | Flexibility |
|--------|-------|-----------|------------|
| UI Filters | Fast | Low | Basic |
| Tags | Fast | Low | Limited |
| Session/User ID | Very Fast | Very Low | Medium |
| Metadata | Medium | Medium | High |
| Full-text Search | Medium | Low | Medium |
| Metrics API | Slow | High | Maximum |

### When to Use Each
| Scenario | Method | File |
|----------|--------|------|
| Find one conversation | Session ID | Guide Sec 1 |
| Find all user's traces | User ID | Guide Sec 2 |
| Look for error messages | Full-text search | Guide Sec 4 |
| Group by category | Tags | Guide Sec 6 |
| Find errors only | Level filter | Guide Sec 7 |
| Complex analysis | Metrics API | Guide (Advanced) |

---

## ✅ Verification Checklist

Before deploying with Langfuse, verify:

- [ ] LANGFUSE_PUBLIC_KEY set in environment
- [ ] LANGFUSE_SECRET_KEY set in environment
- [ ] LANGFUSE_HOST configured (default: cloud.langfuse.com)
- [ ] setup_observability() called in agent entrypoint
- [ ] session_id passed in metadata
- [ ] user_id added to traces during execution
- [ ] Test call made and appears in Langfuse dashboard
- [ ] Filters work (session ID, user ID)
- [ ] Can see trace structure with observations

---

## 📞 Support & Questions

If documentation doesn't answer your question:

1. Check Langfuse official docs: https://langfuse.com/docs/
2. Search Langfuse GitHub discussions
3. Open GitHub issue with specific example
4. Check LiveKit Agents docs for integration specifics

---

## 📝 Documentation Metadata

**Last Updated:** October 31, 2024

**Scope:** PandaDoc Voice AI Trial Success Agent

**Covers:**
- Langfuse version: Current (as of Oct 2024)
- LiveKit Agents: Python SDK
- OpenTelemetry: Integration via OTLPSpanExporter
- Use case: Voice agent observability and debugging

**Status:** Complete - covers all major search and filtering features

---

## 🔗 Related Documentation

Also see in your docs folder:

- `/docs/implementation/observability/` - Other observability guides
- `/my-app/AGENTS.md` - LiveKit agent development guide
- `/docs/specs/PANDADOC_VOICE_AGENT_SPEC_STREAMLINED.md` - Business requirements

---

**Start with:** LANGFUSE_SEARCH_FILTERING_GUIDE.md → LANGFUSE_QUICK_REFERENCE.md

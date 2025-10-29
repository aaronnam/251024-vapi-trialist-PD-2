# Archived Documentation

This directory contains historical work-in-progress notes, debugging records, and analysis documents preserved for reference.

**Purpose**: These documents provide historical context and may be useful if similar issues recur, but they are not part of the active development guides.

---

## Archived Documents

### Test Failure Analysis Reports

#### `test-failure-report.md`
**Date**: October 27, 2025
**Contents**: Analysis of test failures during Google Calendar booking feature implementation

- Test failure categories and summary
- Root cause analysis (tool discovery, LLM judge sensitivity, legacy issues)
- Specific failed tests with expected vs. actual results
- Investigation findings

**Use when**: Understanding how test failures were debugged or if similar patterns recur

---

#### `test-failure-deep-analysis.md`
**Date**: October 27, 2025
**Contents**: Deep dive into root causes of test failures

- Detailed analysis of each failure category
- Tool discovery issues and investigation
- LLM judge sensitivity patterns
- Legacy test issues
- Comprehensive failure breakdowns

**Use when**: Investigating similar test failures or understanding complex test behavior patterns

---

#### `test-results-after-fix.md`
**Date**: October 27, 2025
**Contents**: Test results and improvements after implementing fixes

- Before/after test pass rates
- Which fixes improved which tests
- Remaining failures and next steps
- Performance metrics

**Use when**: Understanding test improvement progression or verifying similar fixes

---

## How to Use Archived Documentation

### If Tests Are Failing
1. Check current test suite with `uv run pytest`
2. If failures match old patterns, consult the deep analysis
3. Review old fixes in the analysis documents
4. Apply or adapt solutions as needed

### For Historical Context
- These documents show how issues were investigated
- Useful for understanding problem-solving approaches
- Good reference for similar future debugging efforts

### When Adding Tests
- Review test failure analysis to understand what patterns are tricky
- Use insights to write better tests from the start
- Reference solutions that worked in past

## Moving Forward

### When to Promote from Archive
If an archived document becomes relevant again:
1. Update with current date and findings
2. Move back to main docs/ directory
3. Update [../README.md](../README.md) with new reference

### When to Delete from Archive
Archived documents can be deleted if:
- 6+ months have passed
- Issue has not recurred
- Similar patterns have been identified and fixed
- Document adds no historical value

---

## Archive Policy

Documents are moved to `.archived/` when they are:
- Work-in-progress or debugging notes
- Historical records of specific point-in-time issues
- Testing/analysis records that become outdated
- No longer actively referenced

This keeps the main documentation clean while preserving valuable historical context.

---

**Last Updated**: October 29, 2025
**Archive Purpose**: Historical reference and context preservation

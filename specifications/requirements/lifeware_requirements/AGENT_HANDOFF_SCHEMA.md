# AGENT_HANDOFF_SCHEMA.md

This file defines the required structure for agent-to-agent handoff files.

Default handoff file name:
NEXT_AGENT_HANDOFF.md

Role-specific handoff files may also be used:
ARCHITECT_HANDOFF.md
DEVELOPER_HANDOFF.md
AUDIT_HANDOFF.md
QA_HANDOFF.md

If multiple handoff files exist, agents should read the most role-relevant file first and then the general handoff.

--------------------------------------------------

# NEXT AGENT HANDOFF

## Agent Role
Architect | Developer | Auditor | QA

## Timestamp
[ISO timestamp if available]

## Build / Package Reviewed
[name of ZIP file or build version]

--------------------------------------------------

## Summary
Short description of what happened in this pass.

--------------------------------------------------

## Current Development Phase
Example:
PHASE 1 — Projects MVP Foundation

--------------------------------------------------

## Requirements Confirmed
List the major requirements verified or preserved.

--------------------------------------------------

## Files Reviewed
List files inspected during this pass.

--------------------------------------------------

## Files Modified
List all modified files, or state: No files modified.

--------------------------------------------------

## Key Decisions
Document important reasoning decisions.

--------------------------------------------------

## Risks / Watch Areas
List areas the next agent should pay attention to.

--------------------------------------------------

## Validation Performed
List the checks that were performed.

--------------------------------------------------

## Expected Behavior After This Pass
Explain the expected system behavior.

--------------------------------------------------

## Recommended Next Agent Role
Architect | Developer | Auditor | QA

--------------------------------------------------

## Recommended Next Action
Explain what the next agent should do.

--------------------------------------------------

## Smoke Test Focus (If Code Changed)
List the key tests the next role should prioritize.

--------------------------------------------------

## Additional Notes
Any useful context that does not fit the sections above.

--------------------------------------------------

End of handoff

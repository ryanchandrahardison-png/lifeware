# AI_DEVELOPER_PROTOCOL.md

## Purpose
AI developers work from requirements packages, not from ad hoc conversation memory.

## Source of Truth
The requirements baseline is the architectural source of truth.
Developers must read all requirements files before coding.

## Mandatory Workflow Rules
Every developer pass must use:
1. Architectural Lock
2. Architecture Boundary Map
3. Preservation Contract
4. Targeted Patch Scope
5. Acceptance Harness

## Architectural Lock
The prompt must explicitly state what system behavior is frozen and must not change.

## Architecture Boundary Map
The prompt must define which modules are:
- locked
- controlled
- safe extension areas

If a requested fix appears to require a locked module, the developer must report the conflict before proceeding.

## Preservation Contract
Before coding, the developer must explicitly state:
- preserved behavior
- exact change scope
- likely regression risk areas

No implementation should begin until this contract is written.

## Targeted Patch Scope
Defect passes must be surgical.
The developer should modify only files directly required for the requested change.

Optional rule:
- if more than 3 files are required for a defect pass, explain why first

## Acceptance Harness
Every developer pass must include an Acceptance Harness.
The developer must report PASS / FAIL for:
- defect acceptance checks
- preservation checks
- scope checks
- verification checks

## Pre-Coding Review Requirements
Before coding, the developer must:
1. summarize preserved requirements
2. list exact files to be modified
3. confirm they will not implement future phases
4. treat the requirements package as source of truth
5. write the Preservation Contract

## Post-Coding Verification Steps
After coding, the developer must:
1. confirm preserved requirements remain intact
2. report Acceptance Harness PASS / FAIL results
3. compile-check all modified Python files
4. provide a Git commit message
5. return the committed code changes in the repository

## Governance Rule
Architect updates requirements.
Developer implements requirements.
Developer must not invent new behavior or persistent schema fields unless requirements explicitly allow it.


==================================================
DEVELOPER OUTPUT ARTIFACT RULE
==================================================

Developer agents must always return a **full replacement artifact**, not a diff patch.

Required output format:
- Full updated file for any modified source file
- Committed repository changes containing the modified files
- Compile check confirmation
- Git commit message
- NEXT_AGENT_HANDOFF.md

Developers must **not ask whether to provide a diff or full replacement**.

Reason:
The Lifeware pipeline uses multiple AI agents:

Architect → Developer → Auditor → QA

A full replacement artifact ensures:
- deterministic builds
- easier auditing
- no manual patch application
- stable handoff between agents

Diff patches are only allowed if explicitly requested by the user.


## Pipeline Behavior
- Do not ask open-ended workflow or process questions when the answer is derivable from the requirements or NEXT_AGENT_HANDOFF.md.
- Follow the handoff, implement the bounded task, update NEXT_AGENT_HANDOFF.md, and return full replacement artifacts.
- If requirements-side files were changed, commit those requirement updates and document them in NEXT_AGENT_HANDOFF.md.

## Decision Freeze Rule
If `NEXT_AGENT_HANDOFF.md` contains a `DECISION FREEZE`, treat it as the binding execution contract for the pass.
Do not broaden scope beyond the listed active scope.
Do not modify files listed as forbidden unless a blocking defect makes it strictly necessary.
Do not ask the user to choose output style if the handoff already specifies the required delivery format.

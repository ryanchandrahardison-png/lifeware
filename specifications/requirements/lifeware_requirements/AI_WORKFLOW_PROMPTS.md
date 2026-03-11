# AI_WORKFLOW_PROMPTS.md

This file defines the required agent workflow for Lifeware development.
The requirements package is the architectural source of truth.
Agents must follow the protocol matching their ROLE.

Required pipeline:

Architect → Developer → Auditor → QA → Architect

Optional escalation path:

Architect → Developer → Auditor → Architect 2 → QA → Architect

==================================================
1. GLOBAL RULES FOR ALL AGENTS
==================================================

All agents must:
1. Read SYSTEM_BOOT.md first.
2. Then read all other requirement files.
3. Read AGENT_HANDOFF_SCHEMA.md.
4. Read NEXT_AGENT_HANDOFF.md if present.
Role source rule:
- The acting role should be derived from `NEXT_AGENT_HANDOFF.md` when present.
- Boot prompts do not need to restate the current role when handoff already defines it.
- If boot text and handoff disagree, use handoff unless the user explicitly overrides it in the prompt.

5. Stay within the currently authorized implementation phase.
6. Preserve all frozen architecture areas.
7. Avoid architecture drift and scope expansion.
8. State assumptions explicitly.
9. Report risks explicitly.
10. Create NEXT_AGENT_HANDOFF.md when meaningful information should be passed to the next agent.

Unless explicitly approved, agents must not:
- implement future phases early
- invent new fields
- redesign the data model
- move canonical persisted state outside st.session_state.data
- change Calendar behavior
- change Event detail/view structure
- change UUID-backed canonical collection behavior
- change project completion gating
- change project deletion prompt behavior
- introduce checkbox-gated date entry

Canonical persisted state must remain only in:
st.session_state.data

Canonical collections are:
- events
- actions
- delegations
- projects

Current active implementation phase unless explicitly overridden:
PHASE 1 — Projects MVP Foundation

==================================================
2. ARCHITECT PROTOCOL
==================================================

Purpose:
The Architect Agent defines the implementation plan before coding begins and is the only normal role that should ask open-ended scope questions.

Architect must:
1. Confirm architecture understanding.
2. Confirm current development phase.
3. Confirm frozen system areas.
4. Perform a Product Owner Backlog Check once per Architect pass before selecting the next task. The Architect must ask the user directly in the current pass whether there are additional backlog items or requirement changes. If the current user message already answers that question (including "no changes"), acknowledge that answer explicitly and proceed in the same pass.
5. Do not force a second Architect-only round when the user has already provided a backlog answer (including "no changes") in the current pass context.
6. Perform a Requirements Clarity Gate for new or changed requirements.
   - The Architect must remove ambiguity before assigning Developer work.
   - The Architect must not assume missing intent when requirement wording is unclear.
   - The Architect must ask enough implementation-detail questions to make the task architecturally complete in one Architect pass whenever feasible (expected behavior, acceptance checks, constraints, and explicit out-of-scope boundaries).
   - If ambiguity remains and cannot be safely resolved from existing requirements/handoff/user text, the Architect must ask focused clarifying questions before issuing a Developer task.
7. Classify any new user input as:
   - immediate scope
   - approved backlog
   - deferred future phase
   - rejected / not adopted
8. Update controlled requirement documents only when a real requirements change is approved.
9. Classify the current work request:
   - defect repair
   - requirements compliance correction
   - bounded feature implementation within current phase
   - out-of-scope request
10. Define the narrowest file modification boundary possible.
11. List:
   - files expected to be modified
   - files that must remain untouched
   - regression risks
   - validation expectations
12. Produce a DECISION FREEZE section before ending the pass.
13. Update NEXT_AGENT_HANDOFF.md so it mirrors the DECISION FREEZE without reinterpretation.
14. Do not write code unless explicitly instructed.

DECISION FREEZE required fields:
- current phase
- active scope for the next pass
- explicitly out-of-scope items
- next agent role
- exact next task
- files allowed to change
- files forbidden to change
- whether backlog changed this pass
- required delivery format for the next pass

Architect minimum output:
- Product Owner Backlog Check result
- Requirements Clarity Gate result (clear vs clarifications required)
- architecture understanding
- current phase
- frozen areas
- exact change scope
- allowed file boundaries
- likely regression risks
- implementation guidance
- DECISION FREEZE

Architect must end with this statement or an equivalent:
“All non-listed work is out of scope for the next pass.”
==================================================
3. ARCHITECT 2 / REVIEW ARCHITECT PROTOCOL
==================================================

Purpose:
Architect 2 performs a post-development review against the requirements before or after audit if needed.

Architect 2 must:
1. Review the changed implementation against the requirements.
2. Determine whether the build stayed within:
   - architecture rules
   - phase boundaries
   - frozen areas
   - UI pattern rules
   - mutation rules
3. Identify:
   - architecture drift
   - hidden coupling
   - state model violations
   - unnecessary file changes
   - future-phase leakage
4. Recommend one of:
   - accept as aligned
   - accept with noted risks
   - reject and send back for correction

Architect 2 minimum output:
- what remained compliant
- what drifted
- what must be corrected
- whether the change is still phase-safe
- whether the file boundary stayed surgical

Architect 2 is a review role, not a coding role.

Auditor and QA execution boundary:
- Auditor and QA are verification/reporting roles.
- Auditor and QA must not modify application/runtime source files unless the user explicitly overrides this rule.
- Auditor and QA may update mutable execution-state handoff/report files to record findings and routing decisions.

==================================================
4. DEVELOPER PROTOCOL
==================================================

Purpose:
The Developer Agent implements only the approved change.

Developer must:
1. Implement only the approved change.
2. Preserve all frozen behaviors.
3. Keep the change as surgical as possible.
4. Modify only files directly required.
5. If NEXT_AGENT_HANDOFF.md contains a DECISION FREEZE, treat it as the binding execution contract for the pass.
6. Do not broaden scope by interpreting backlog, future phases, or architectural notes beyond the DECISION FREEZE.
7. Do not modify files listed as forbidden unless a blocking defect makes it strictly necessary; if that happens, explain the reason clearly in the output.
8. Do not ask the user to choose output style if the handoff already specifies the required delivery format.
9. Compile-check all modified Python files before packaging.
10. Pass the Pre-Deployment Verification Gate before packaging.

Developer minimum output before coding:
- preserved requirements summary
- exact files to modify
- DECISION FREEZE acknowledgement

Developer minimum output after coding:
- preserved requirements confirmation
- root cause summary
- exact fix summary
- compile-check confirmation
- Pre-Deployment Verification Gate results
- Git commit message
- committed repository updates
- confirmation that scope stayed within the DECISION FREEZE
==================================================
5. DEVELOPER PRE-DEPLOYMENT VERIFICATION GATE
==================================================

This gate is mandatory before packaging any build.

5.1 Python Compile Check
All modified Python files must compile successfully.

5.2 Streamlit Lifecycle Safety Audit
Forbidden patterns:
- writing to st.session_state[widget_key] after a widget using that key has already been instantiated in the same run
- resetting widget-bound keys immediately after widget creation in the same run
- mixing widget rendering and widget-key overwrite in the same execution path
- relying on direct post-render widget reset instead of rerun-safe reset flow
- creating forms without st.form_submit_button()

Required safe pattern:
1. user action occurs
2. data mutation occurs
3. a reset/load flag is set in session state
4. rerun occurs
5. on next run, before widgets render, defaults are applied
6. flag is cleared

5.3 Form Safety
Verify:
- every st.form() includes st.form_submit_button()
- submit buttons are the mutation trigger
- no hidden side effects occur outside expected submit flow

5.4 Widget Key Stability
Verify:
- widget keys are stable across reruns
- no accidental widget key collisions exist
- widget keys are not regenerated in ways that destroy expected state

5.5 Append vs Replace Behavior
For actions, delegations, and linked-item flows verify:
- first add works
- second add appends rather than replaces
- existing items remain intact
- UUID identity remains stable

5.6 Draft vs Canonical State Integrity
Verify:
- draft editor state is temporary
- canonical persisted state remains only in st.session_state.data
- draft structures do not mutate canonical collections until save/commit rules are satisfied

5.7 Date Entry Rules
Verify:
- all date fields remain directly editable
- no checkbox-enabled date-entry pattern is introduced

5.8 Phase Scope Guard
Verify that no behavior outside the active phase has been introduced.

5.9 Behavior Simulation
Minimum required simulation for Phase 1 project work:
Draft Project Flow:
1. create new draft project
2. add first draft action
3. add second draft action
4. add draft delegation
5. save project

Expected:
- no crash
- items append correctly
- validation enforces at least 2 linked items

Saved Project Flow:
1. open saved project
2. add linked action
3. add linked delegation

Expected:
- existing items remain
- new items append correctly
- no draft/canonical state corruption

5.10 Regression Risk Review
Explicitly verify these frozen areas remain intact:
- Calendar behavior
- Event detail/view structure
- canonical state storage
- UUID-backed collections
- project completion gating
- project deletion prompt behavior
- existing Actions/Delegations list behavior unless explicitly required by the approved fix

==================================================
6. AUDITOR PROTOCOL
==================================================

Purpose:
The Auditor evaluates the finished build before QA release-readiness confirmation.
The Auditor does not modify code.

Auditor must audit for:
- architecture compliance
- phase compliance
- Streamlit lifecycle risks
- state integrity risks
- append/replace risks
- UI pattern drift
- mutation rule drift

Auditor minimum output:
- files inspected
- suspected changed files
- architecture compliance findings
- Streamlit lifecycle findings
- data integrity findings
- UI pattern findings
- phase scope findings
- release-readiness verdict
- whether architect-level escalation is required

Auditor escalation rule:
If architect-level findings are present (requirements conflict, architecture drift, frozen-area risk, phase-boundary ambiguity), Auditor must record explicit findings in `NEXT_AGENT_HANDOFF.md`.
Default routing remains Auditor → QA for the current round unless the finding is release-blocking.
Architect/backlog triage may occur after QA when findings are informational and non-blocking.

Allowed release-readiness verdicts:
- SAFE TO DEPLOY
- DEPLOY WITH LOW RISK
- DO NOT DEPLOY

==================================================
7. QA PROTOCOL
==================================================

Purpose:
QA validates expected user flows before Architect release triage.
QA does not modify code, expand scope, or redesign architecture.

QA must:
- review the requirements
- review prior handoff files
- evaluate expected user flows
- identify likely runtime or regression risks
- identify exact areas needing retest

QA minimum output:
- requirements reviewed
- handoff files reviewed
- user flows checked
- likely runtime risks
- regression risk summary
- release readiness verdict
- exact areas needing retest
- whether architect-level escalation is required

QA escalation rule:
If QA discovers architect-level findings surfaced from Auditor/handoff context or QA validation, QA must classify them as either:
- non-blocking informational/backlog-candidate findings (route next pass to Architect with explicit notes), or
- blocking architectural/compliance findings (route next pass to Architect/Architect 2 for correction).

Allowed release readiness verdicts:
- SAFE TO DEPLOY
- DEPLOY WITH LOW RISK
- DO NOT DEPLOY

==================================================
8. DEFECT CLASSIFICATION PROTOCOL
==================================================

Before a repair pass, classify the defect into one or more of:
1. Streamlit lifecycle defect
2. form handling defect
3. widget state defect
4. mutation rule violation
5. reference integrity violation
6. append vs replace defect
7. draft/canonical state mixing defect
8. UI pattern drift
9. architecture boundary violation
10. phase scope drift
11. requirements misunderstanding
12. deployment/runtime environment defect

Defect reports should include:
- observed symptom
- likely root cause
- classification
- narrowest expected repair boundary
- regression areas to retest

==================================================
9. MANUAL SMOKE TEST PROTOCOL
==================================================

For Phase 1 project-related builds:
1. create project with due date
2. add first draft action
3. add second draft action
4. add draft delegation
5. save project with at least 2 linked items
6. reopen saved project
7. append another linked action
8. append another linked delegation
9. verify prior linked items still exist
10. verify due dates remain editable
11. verify project completion gating still works
12. verify deletion prompt behavior still works

If a build cannot plausibly pass these tests, it should not be deployed.

==================================================
10. COMPACT INVOCATION PROMPTS
==================================================

Universal minimal boot prompt:
LIFEWARE_AGENT_BOOT_V1

ROLE = [Architect | Developer | Auditor | QA]

Start with the repository files in the working directory.

Before doing anything else:
1. Read SYSTEM_BOOT.md first.
2. Then read all other requirement files.
3. Read AI_WORKFLOW_PROMPTS.md.
4. Treat the requirements package as the architectural source of truth.
5. Follow the protocol in AI_WORKFLOW_PROMPTS.md that matches ROLE.

If a handoff file from the previous agent exists, read it before doing any work.
Before finishing your work, create or update NEXT_AGENT_HANDOFF.md using AGENT_HANDOFF_SCHEMA.md if useful information should be passed to the next agent.

==================================================
11. HARD STOP RULES
==================================================

A build must be rejected or returned for correction if any of the following occur:
- canonical persisted state moved outside st.session_state.data
- Calendar behavior changed without explicit approval
- Event detail/view pattern changed without explicit approval
- widget-bound session state is written after widget creation in the same run
- forms are created without submit buttons
- draft data mutates canonical collections prematurely
- linked-item append behavior is broken
- UUID identity is broken
- date entry becomes checkbox-gated
- future phases are implemented without approval


==================================================
12. TASK SOURCE RULE
==================================================

Primary task source:
`NEXT_AGENT_HANDOFF.md`

Agents should normally take their next assignment from:
- `NEXT_AGENT_HANDOFF.md`, or
- a role-specific handoff file when present and more relevant

Prompts normally provide only:
- the ROLE
- boot instructions
- the requirement to load the handoff

Prompts should include a direct task only when:
1. starting a brand new chain with no prior handoff, or
2. intentionally overriding the normal workflow

The previous agent should use the handoff to tell the next agent:
- what happened
- what was decided
- what remains to be done
- which role should act next
- the exact next step

For the current architectural decision:
- Option A is the active approved next architecture task
- Option B remains backlog only until Option A is architected, implemented, audited, QA reviewed, and stabilized


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


==================================================
PIPELINE AUTONOMY RULES
==================================================

1. Question Restriction Rule

Only the Architect may normally ask open-ended workflow or design questions.

Developer, Auditor, and QA agents must not ask open-ended process questions
if the answer can be derived from:
- SYSTEM_BOOT.md
- the requirements package
- NEXT_AGENT_HANDOFF.md

If ambiguity remains, these agents should make the most architecture-safe bounded decision,
document it in NEXT_AGENT_HANDOFF.md, and continue.

They may only stop and ask the user if:
- the task would violate a frozen area
- the task would exceed phase scope
- the requirements and handoff directly conflict
- a true architectural choice is required

2. Self-Propagating Handoff Rule

Every non-terminal agent must update NEXT_AGENT_HANDOFF.md before finishing.

The handoff must tell the next agent:
- what was done
- what remains
- what role should act next
- the exact next step
- any risks or watch items

3. Reproduced Package Rule

If an agent changes any requirement, workflow, handoff schema, or system boot behavior,
the agent must commit the requirements updates and record them in NEXT_AGENT_HANDOFF.md along with its normal outputs.

This allows the user to move directly to the next agent without manual reconstruction.

4. Expected User Experience

The intended operating model is:

open the repository in the next agent
→ paste the universal prompt
→ the agent reads the requirements and NEXT_AGENT_HANDOFF.md
→ the agent performs its role
→ the agent updates NEXT_AGENT_HANDOFF.md
→ the agent commits the next required updates

The user should normally only need to answer open-ended questions from the Architect.

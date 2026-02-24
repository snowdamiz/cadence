---
name: cadence
description: Structured project operating system for end-to-end greenfield or brownfield delivery. Use when users want the AI to guide the full lifecycle from initialization, requirements, roadmap, and phased execution through milestone audit and completion with deterministic gates, traceability, and rollback-safe execution.
---

# Cadence

## Overview
1. Keep this root skill as an orchestrator.
2. Delegate concrete execution to focused subskills.

## Response Hygiene
1. Keep user-facing replies outcome-focused and concise.
2. Do not expose internal execution details unless the user explicitly asks for them:
   - skill routing chains
   - gate-by-gate status narration
   - raw commands, terminal traces, or timing metadata
3. When internal gates/checks succeed, continue directly with the user task and do not announce that checks were run.

## State Mutation Safety
1. Never manually edit `.cadence/cadence.json`.
2. Mutate Cadence state only through the provided Cadence scripts (for example `run-*-gate.py`, `inject-ideation.py`, `run-brownfield-documentation.py`, `run-research-pass.py`, `set-workflow-item-status.py`, `read-workflow-state.py`).
3. If a required state transition is not supported by existing scripts, stop and update scripts first instead of writing JSON by hand.
4. For subskill preflight setup (project root + scripts-dir + repo-status, with optional route/workflow checks), use `scripts/run-skill-entry-gate.py` instead of repeating command chains.

## Repo Status Gate
1. At Cadence entry (first assistant response in the conversation), resolve `PROJECT_ROOT` with `python3 scripts/resolve-project-root.py --project-root "$PWD"` (resolve script paths from this skill directory but keep command cwd at the active project).
2. If `"$PROJECT_ROOT/.cadence"` exists, run `python3 scripts/check-project-repo-status.py --project-root "$PROJECT_ROOT"`.
3. Never run `check-project-repo-status.py` without `--project-root`; this invocation is intentionally treated as ambiguous from the skill directory.
4. If `"$PROJECT_ROOT/.cadence"` does not exist, skip this gate at root entry and let `skills/scaffold/SKILL.md` establish repo mode after scaffold initialization.
5. Read `repo_enabled` from script output and treat it as the authoritative push mode for the active subskill conversation.
6. If `repo_enabled` is false, continue with local commits only until a GitHub remote is configured.
7. Do not rerun this gate between normal user replies inside the same active subskill conversation.
8. Rerun this gate only when:
   - starting a new Cadence conversation
   - transitioning to a different subskill after a completed checkpoint
   - handling explicit resume/status/reroute requests
   - recovering from a gate/assertion failure

## Git Checkpoints
1. Enforce Cadence commit convention from `config/commit-conventions.json`.
2. At the end of each successful subskill conversation, run `scripts/finalize-skill-checkpoint.py` with configured `--scope` and `--checkpoint` values.
3. `finalize-skill-checkpoint.py` must check git diff first, split changes into atomic semantic batches, and create multiple small checkpoint commits when needed before push.
4. `finalize-skill-checkpoint.py` must use repo status output so commits are local-only when `repo_enabled` is false.
5. Use `--paths .` unless a narrower path is explicitly required, so commits include any files changed by the skill.
6. Treat checkpoint or push failures as blocking; surface the exact script error to the user.
7. If finalization returns `status=no_changes`, continue without failure.
8. Do not gate checkpoint commits on test results yet; add that gate only when explicitly introduced later.

## Scaffold Gate (Mandatory On First Turn)
1. Check for `.cadence` in the project root.
2. If `.cadence` is missing, invoke `skills/scaffold/SKILL.md`.
3. Scaffold initializes and persists `state.cadence-scripts-dir` for later subskill commands.
4. If `.cadence` exists but `.cadence/cadence.json` is missing, invoke `skills/scaffold/SKILL.md` for recovery.
5. If both `.cadence` and `.cadence/cadence.json` exist, skip scaffold.

## Workflow Route Gate (Mandatory At Entry And Transitions)
1. After scaffold handling on Cadence entry, run `python3 scripts/read-workflow-state.py --project-root "$PROJECT_ROOT"` and parse the JSON response.
2. Treat `next_item` and `route.skill_name` from that response as the authoritative workflow route.
3. Do not invoke a state-changing subskill unless it matches `route.skill_name`.
4. Keep the active route stable during normal multi-turn ideation/research conversation flow; do not rerun route reads between ordinary user answers.
5. Rerun `read-workflow-state.py` only when:
   - a subskill checkpoint completed and Cadence needs the next route
   - user explicitly asks to continue/resume/status/reroute
   - a route assertion failed and recovery is required

## Initial Bootstrap Auto-Run (Mandatory)
1. For first-run bootstrap on a net-new project, automatically execute setup gates in one continuous flow: `scaffold` -> `prerequisite-gate` -> project mode intake (`brownfield-intake`).
2. After each successful setup gate checkpoint, rerun `read-workflow-state.py` and immediately continue with the next routed setup gate in the same turn.
3. Do not stop after scaffold or prerequisite success just to ask the user to trigger the next gate manually.
4. Pause only when a gate requires an explicit user decision (for example remote configuration or `.cadence` git policy in scaffold).
5. After brownfield-intake completes:
   - if route advances to `ideator`, end with the exact ideation handoff line
   - if route advances to `brownfield-documenter`, end with the exact brownfield handoff line

## Prerequisite Gate (Conditional)
1. Invoke `skills/prerequisite-gate/SKILL.md` only when `route.skill_name` is `prerequisite-gate`.
2. If `route.skill_name` is not `prerequisite-gate` (for example `brownfield-intake`, `brownfield-documenter`, `ideator`, `researcher`, or `planner`), skip prerequisite gate and follow the active route instead.

## Project Mode Intake Gate (Conditional)
1. Invoke `skills/brownfield-intake/SKILL.md` only when `route.skill_name` is `brownfield-intake`.
2. Use this gate to classify `greenfield` vs `brownfield` execution mode and capture baseline inventory for existing codebases.
3. If `route.skill_name` is not `brownfield-intake`, skip this gate and follow the active route instead.
4. In user-facing wording, call this step `project mode intake`; avoid calling the project brownfield until mode resolution returns `brownfield`.

## Brownfield Documentation Gate (Conditional)
1. Invoke `skills/brownfield-documenter/SKILL.md` only when `route.skill_name` is `brownfield-documenter`.
2. Use this gate to document the existing project into the canonical ideation and research agenda structures before researcher routing.
3. If `route.skill_name` is not `brownfield-documenter`, skip this gate and follow the active route instead.

## Progress / Resume Flow
1. Invoke `skills/project-progress/SKILL.md` when the user asks to continue/resume or requests progress status (for example: "continue the project", "how far along are we?", "where did we leave off?").
2. Use that skill's state-based routing result to continue from the correct next phase.

## Manual Subskill Safety Gate
1. If the user manually requests a Cadence subskill, first resolve `PROJECT_ROOT` with `python3 scripts/resolve-project-root.py --project-root "$PWD"`.
2. Run `python3 scripts/assert-workflow-route.py --skill-name <subskill> --project-root "$PROJECT_ROOT"` before executing that subskill.
3. Ensure that direct subskill execution still applies this skill's Repo Status Gate and Git Checkpoints rules.
4. If route assertion fails, stop and surface the exact script error.
5. Do not execute state-changing subskill steps when assertion fails.

## Ideation Flow
1. When scaffold, prerequisite, and project mode intake complete in this same conversation for a net-new project and route advances to `ideator`, force a subskill handoff and end with this exact line: `Start a new chat and either say "help me define my project" or share your project brief.`
2. In subsequent conversations, if the workflow route is `ideator`, do not rerun prerequisite gate or project mode intake.
3. If the user asks to define the project or provides a brief while route is `ideator`, invoke `skills/ideator/SKILL.md`.
4. If route is `ideator` and the user has not provided ideation input yet, ask one kickoff ideation question in-thread and continue.
5. When route advances from `ideator` to `researcher`, force a handoff and end with this exact line: `Start a new chat with a new agent and say "research my project".`

## Brownfield Flow
1. When scaffold, prerequisite, and project mode intake complete in this same conversation for a brownfield project and route advances to `brownfield-documenter`, force a subskill handoff and end with this exact line: `Start a new chat and say "document my existing project".`
2. In subsequent conversations, if workflow route is `brownfield-documenter`, invoke `skills/brownfield-documenter/SKILL.md`.
3. Do not route brownfield projects to `skills/ideator/SKILL.md` unless the user explicitly asks to run net-new ideation discovery.
4. When route advances from `brownfield-documenter` to `researcher`, force a handoff and end with this exact line: `Start a new chat with a new agent and say "research my project".`

## Research Flow
1. If the workflow route is `researcher`, invoke `skills/researcher/SKILL.md`.
2. Enforce one research pass per conversation so context stays bounded.
3. When the researcher flow reports additional passes remain (`handoff_required=true`), end with this exact line: `Start a new chat and say "continue research".`
4. Continue routing to researcher on subsequent chats until workflow reports the research task complete.
5. For greenfield projects, when research completes and route advances to `planner`, invoke `skills/planner/SKILL.md` in the next routed conversation.

## Planner Flow
1. If the workflow route is `planner`, invoke `skills/planner/SKILL.md`.
2. Planner is greenfield-only and should not run for brownfield routes.
3. Keep planner output at milestone/phase level in `.cadence/cadence.json` and defer waves/tasks decomposition to a later planning subskill.

## Ideation Update Flow
1. If the user wants to modify or discuss existing ideation, invoke `skills/ideation-updater/SKILL.md`.
2. Use this update flow only for existing project ideation changes; use the new-chat handoff in Ideation Flow for net-new ideation discovery.

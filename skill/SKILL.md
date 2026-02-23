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

## Repo Status Gate
1. At the start of every Cadence turn, run `python3 scripts/check-project-repo-status.py` (resolve this relative path from this skill directory).
2. Read `repo_enabled` from script output and treat it as the authoritative push mode.
3. If `repo_enabled` is false, continue with local commits only until a GitHub remote is configured.

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
4. If `.cadence` exists, skip scaffold.

## Workflow Route Gate (Mandatory Every Turn)
1. After scaffold handling, run `python3 scripts/read-workflow-state.py` and parse the JSON response.
2. Treat `next_item` and `route.skill_name` from that response as the authoritative workflow route.
3. Do not invoke a state-changing subskill unless it matches `route.skill_name`.

## Prerequisite Gate (Conditional)
1. Invoke `skills/prerequisite-gate/SKILL.md` only when `route.skill_name` is `prerequisite-gate`.
2. If `route.skill_name` is not `prerequisite-gate` (for example `ideator` or `researcher`), skip prerequisite gate and follow the active route instead.

## Progress / Resume Flow
1. Invoke `skills/project-progress/SKILL.md` when the user asks to continue/resume or requests progress status (for example: "continue the project", "how far along are we?", "where did we leave off?").
2. Use that skill's state-based routing result to continue from the correct next phase.

## Manual Subskill Safety Gate
1. If the user manually requests a Cadence subskill, first resolve `PROJECT_ROOT` with `python3 scripts/resolve-project-root.py`.
2. Run `python3 scripts/assert-workflow-route.py --skill-name <subskill> --project-root "$PROJECT_ROOT"` before executing that subskill.
3. If route assertion fails, stop and surface the exact script error.
4. Do not execute state-changing subskill steps when assertion fails.

## Ideation Flow
1. When scaffold and prerequisite both complete in this same conversation for a net-new project, hand off to a fresh chat so context resets cleanly.
2. Use this exact handoff line: `Start a new chat and either say "help me define my project" or share your project brief.`
3. In subsequent conversations, if the workflow route is `ideator`, do not rerun prerequisite gate.
4. If the user asks to define the project or provides a brief while route is `ideator`, invoke `skills/ideator/SKILL.md`.
5. If route is `ideator` and the user has not provided ideation input yet, prompt with the same handoff line and wait.

## Research Flow
1. If the workflow route is `researcher`, invoke `skills/researcher/SKILL.md`.
2. Enforce one research pass per conversation so context stays bounded.
3. When the researcher flow reports additional passes remain, end with the exact handoff line: `Start a new chat and say "continue research".`
4. Continue routing to researcher on subsequent chats until workflow reports the research task complete.

## Ideation Update Flow
1. If the user wants to modify or discuss existing ideation, invoke `skills/ideation-updater/SKILL.md`.
2. Use this update flow only for existing project ideation changes; use the new-chat handoff in Ideation Flow for net-new ideation discovery.

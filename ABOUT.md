# ABOUT: Cadence

## What This Project Is
Cadence is an **installable AI skill system** (published as `cadence-skill-installer`) that adds a deterministic, stateful project workflow to multiple AI tools (Codex, Claude, Gemini, Copilot variants, Windsurf, OpenCode).  
This repo is **not** an app/product runtime; it is a packaged skill + script toolkit.

Core idea: turn ad-hoc assistant behavior into a repeatable project operating system with:
- explicit lifecycle gates
- persisted workflow state (`.cadence/cadence.json`)
- guarded routing between subskills
- structured checkpoint commits (atomic, convention-driven, push-aware)

## Why It Exists
Cadence targets common LLM workflow failure modes:
- no stable memory across turns/chats
- weak phase boundaries (setup vs planning vs execution blur together)
- unsafe/untraceable state changes
- poor resume behavior after interruptions
- inconsistent git hygiene for AI-generated changes

Cadence solves this by making workflow state first-class and script-enforced.

## Repository Shape
Top-level:
- `/Users/sn0w/Documents/dev/cadence/scripts/install-cadence-skill.mjs`: npm CLI installer that copies `skill/` into tool-specific skill dirs.
- `/Users/sn0w/Documents/dev/cadence/skill/`: actual Cadence skill package.
- `/Users/sn0w/Documents/dev/cadence/.github/workflows/publish.yml`: npm publish via GitHub Actions + OIDC trusted publishing.
- `/Users/sn0w/Documents/dev/cadence/package.json`: package metadata (`name: cadence-skill-installer`, `version: 0.2.6`, `type: module`, Node `>=18`).

Install-time payload (what gets copied to user tool skill paths):
- `skill/SKILL.md` (orchestrator policy)
- `skill/skills/*` (subskills: scaffold, prerequisite-gate, ideator, ideation-updater, project-progress)
- `skill/scripts/*` (Python/shell execution engine)
- `skill/config/commit-conventions.json`
- `skill/assets/cadence.json` + `skill/assets/AGENTS.md`

`npm pack --dry-run` shows ~36 files, ~124.7 kB unpacked.

## Operational Model (How It Works)
### 1) Install
`npx cadence-skill-installer` copies `skill/` into selected tool directories under home (example: `~/.codex/skills/cadence`).

Installer behavior:
- supports interactive TUI multi-select + text fallback + non-interactive flags (`--all`, `--tools`, `--yes`, `--home`)
- detects existing installs and warns before overwrite
- recursively copies skill content while skipping `.DS_Store` and `__pycache__`

### 2) Orchestrate (root skill)
`skill/SKILL.md` is intentionally an orchestrator; execution is delegated to subskills/scripts.

Per Cadence turn, high-level policy:
1. Check repo status (`check-project-repo-status.py`) and persist `state.repo-enabled`.
2. If `.cadence` missing: run scaffold gate.
3. Read workflow route (`read-workflow-state.py`) and treat `route.skill_name` as authoritative.
4. Run prerequisite gate only when route points to `prerequisite-gate`; skip it when route has already advanced.
5. Use project-progress skill for resume/status intents.
6. If user manually calls a subskill: resolve project root, then assert workflow route for that root first.
7. For net-new ideation handoff: after scaffold+prereq in-thread, instruct user to start fresh chat for ideation.

Design emphasis:
- deterministic routing
- safety guardrails before state mutation
- user-facing output hygiene (hide internal traces unless requested)

### 3) Persist State
Canonical state file: `.cadence/cadence.json` (inside whichever project root Cadence is operating on).

Default model includes:
- `prerequisites-pass` (bool)
- `state.ideation-completed` (bool)
- `state.cadence-scripts-dir` (absolute helper script dir path)
- `state.repo-enabled` (bool; governs push vs local-only checkpoints)
- `workflow.plan` (nested milestone -> phase -> wave -> task)
- `project-details` and `ideation` objects
- `ideation.research_agenda` with normalized research `blocks`, `entity_registry`, and `topic_index` for later-phase deep research routing/querying

Current default actionable tasks:
- `task-scaffold` -> `scaffold`
- `task-prerequisite-gate` -> `prerequisite-gate`
- `task-ideation` -> `ideator`

### 4) Derive + Route Workflow
`workflow_state.py` is the core state engine:
- normalizes malformed/missing fields
- ensures ideation research agenda defaults exist in canonical shape
- coerces statuses (`pending|in_progress|complete|blocked|skipped`)
- rolls up parent statuses from children
- computes `workflow.summary`, `next_item`, `next_route`, completion percent
- maintains legacy compatibility fields (`next_phase`, `active_phase`, etc.)
- syncs legacy booleans from task status (`prerequisites-pass`, `ideation-completed`)

`assert-workflow-route.py` blocks out-of-order state-changing subskill calls by checking requested skill against computed `next_route.skill_name`.

## Subskills (Functional Intent)
- `scaffold`: create `.cadence`, initialize `cadence.json`, persist scripts-dir, configure `.gitignore` track/ignore policy, initialize git/repo mode, checkpoint.
- `prerequisite-gate`: verify Python availability (`python3`), persist prerequisite pass, checkpoint.
- `ideator`: one-question-at-a-time project ideation, infer a complete domain-agnostic research agenda from the conversation, and treat execution planning as AI-driven by default (if timelines come up, estimate roughly 10-100x faster than human-only delivery without forcing timeline-specific prompts), then persist finalized ideation payload and checkpoint.
- `ideation-updater`: discuss/modify existing ideation, keep research agenda synchronized, persist updated full ideation object, checkpoint.
- `project-progress`: read normalized workflow state, report progress, route next action, checkpoint.

## Script System (Execution Backplane)
Key scripts by concern:

Workflow/state:
- `workflow_state.py`: normalization + derived workflow computation.
- `read-workflow-state.py`: load/reconcile/persist normalized state and emit route payload.
- `set-workflow-item-status.py`: set item status and recalculate all derived fields.
- `assert-workflow-route.py`: enforce legal skill transitions.
- `resolve-project-root.py` + `project_root.py`: resolve active project root (cwd, explicit, or cached hint) so subskills can target the correct repo across chats.

Scaffold/prereq:
- `scaffold-project.sh`: idempotent `.cadence` bootstrap (uses template fallback JSON).
- `run-scaffold-gate.py`: route assert + scaffold + scripts-dir init + state validation.
- `run-prerequisite-gate.py`: route assert + scripts-dir resolve + python check + state write.
- `handle-prerequisite-state.py`: read/write `prerequisites-pass`.
- `resolve-project-scripts-dir.py` + `init-cadence-scripts-dir.py`: self-heal script path state.
- `configure-cadence-gitignore.py`: `.cadence` track/ignore policy updates.

Ideation:
- `ideation_research.py`: shared normalization and validation for ideation research agenda shape and entity/topic/block relationships.
- `prepare-ideation-research.py`: normalize and validate ideation payload research agenda before injection.
- `query-ideation-research.py`: granular query surface for `ideation.research_agenda` by block, topic, entity, category, tag, priority, and text.
- `inject-ideation.py`: validate/merge/replace ideation payload, enforce research agenda requirements when ideation is complete, route-guard when marking complete, optional payload-file deletion.
- `get-ideation.py`, `expose-ideation.py`, `render-ideation-summary.py`: machine/human ideation reads and summaries.

Git checkpoints:
- `check-project-repo-status.py`: detect git+GitHub remote readiness; persist repo mode.
- `git-checkpoint.py`: stage paths, build conventioned commit message, commit, optional push.
- `finalize-skill-checkpoint.py`: split changed files into atomic semantic batches, call `git-checkpoint.py` per batch, honor local-only mode.

## Commit and Traceability Model
`skill/config/commit-conventions.json` defines:
- commit type: `cadence`
- subject max: 72 chars
- scopes/checkpoints (scaffold, prerequisite-gate, ideator, ideation-updater, project-progress)
- atomic batching constraints:
  - max files per commit (default 4)
  - semantic file groups (`cadence-state`, `skill-instructions`, `docs`, `scripts`, `tests`, `config`, `source`)

Finalization behavior:
- inspect working tree (`git status --porcelain`)
- filter by requested pathspecs
- classify files into semantic groups
- chunk into small commits
- commit each chunk with compact suffix tags (`[docs]`, `[scripts2/3]`, etc.)
- push only if `state.repo-enabled=true`; otherwise commit locally (`--skip-push`)

Net effect: deterministic, audit-friendly, rollback-safe checkpoints after each successful subskill conversation.

## Governance and UX Constraints
Cadence instructions consistently require:
- concise, outcome-focused user messaging
- suppression of internal command traces/skill chains unless user explicitly asks
- hard stop on route/assertion failures
- hard stop on checkpoint failures (except explicit `status=no_changes` non-failure path)

`skill/agents/openai.yaml` also injects a default behavior contract for agent UIs (including resume routing and a SOUL persona lookup convention).

## CI/Release Pipeline
- npm publish workflow triggers on `workflow_dispatch` or tag `v*`.
- Uses `actions/setup-node@v4` with Node 24.
- Publishes public package; uses `--provenance` for non-private repos.
- Repo history is release-driven (`v0.1.x` -> `v0.2.6`), with recent work focused on installer UX and safer routing.

## Practical Read of Maturity
What is strong:
- state normalization and backward-compatibility handling are explicit
- route guards reduce accidental phase skipping
- commit automation is unusually disciplined for AI workflows
- installer supports many AI tool ecosystems with one package

What is intentionally narrow right now:
- default workflow tracks only Foundation setup (scaffold/prereq/ideation)
- prerequisite gate currently checks only `python3` presence
- no in-repo automated test suite for scripts yet
- this repo ships framework/instructions; project-specific execution happens in downstream repos that install the skill

## Minimal Mental Model
Cadence = **workflow state machine + guarded skill router + atomic git checkpointer**, wrapped as a cross-tool installable skill package.

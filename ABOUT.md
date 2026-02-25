# ABOUT: Cadence

## What This Project Is
Cadence is an **installable AI skill system** (published as `cadence-skill-installer`) that adds a deterministic, stateful project workflow to multiple AI tools (Codex, Agents, Claude, Gemini, Copilot, GitHub Copilot, Windsurf, OpenCode).  
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
- `/Users/sn0w/Documents/dev/cadence/scripts/clean-python-artifacts.mjs` + `/Users/sn0w/Documents/dev/cadence/scripts/release-preflight.mjs`: release hygiene scripts used by `prepack`/`preversion`.
- `/Users/sn0w/Documents/dev/cadence/skill/`: actual Cadence skill package.
- `/Users/sn0w/Documents/dev/cadence/.github/workflows/publish.yml`: npm publish via GitHub Actions + OIDC trusted publishing.
- `/Users/sn0w/Documents/dev/cadence/package.json`: package metadata (`name: cadence-skill-installer`, `version: 0.2.35`, `type: module`, Node `>=18`, bins: `cadence-skill-installer` + `cadence-install`).

Install-time payload (what gets copied to user tool skill paths):
- `skill/SKILL.md` (orchestrator policy)
- `skill/skills/*` (subskills: scaffold, prerequisite-gate, brownfield-intake, brownfield-documenter, ideator, researcher, planner, ideation-updater, project-progress, project-overview)
- `skill/scripts/*` (Python/shell execution engine)
- `skill/config/commit-conventions.json`
- `skill/assets/cadence.json` + `skill/assets/AGENTS.md`

`npm pack --dry-run` currently shows 62 files, ~399.6 kB unpacked (~76.9 kB tarball).

## Operational Model (How It Works)
### 1) Install
`npx cadence-skill-installer` copies `skill/` into selected tool directories under home (example: `~/.codex/skills/cadence`).

Installer behavior:
- supports interactive TUI multi-select + text fallback + non-interactive flags (`--all`, `--tools`, `--yes`, `--home`)
- checks for `python3` before install; if missing in interactive mode, warns and offers guided installation via detected package manager command
- detects existing installs and warns before overwrite
- recursively copies skill content while skipping `.DS_Store` and `__pycache__`

### 2) Orchestrate (root skill)
`skill/SKILL.md` is intentionally an orchestrator; execution is delegated to subskills/scripts.

Per Cadence turn, high-level policy:
1. Resolve `PROJECT_ROOT` first.
2. If `.cadence` already exists, run repo status (`check-project-repo-status.py --project-root "$PROJECT_ROOT"`) and persist `state.repo-enabled`; if `.cadence` is missing, skip this check until scaffold initializes state.
3. If `.cadence` or `.cadence/cadence.json` is missing: run scaffold gate.
4. Read workflow route (`read-workflow-state.py --project-root "$PROJECT_ROOT"`) and treat `route.skill_name` as authoritative.
5. On first-run bootstrap, auto-chain setup gates in one run (`scaffold` -> `prerequisite-gate` -> project mode intake via `brownfield-intake`) and pause only for explicit user decisions.
6. Run prerequisite gate only when route points to `prerequisite-gate`; skip it when route has already advanced.
7. Run project mode intake when route points to `brownfield-intake` to classify greenfield vs brownfield and capture existing-code baseline.
8. Use project-progress skill for resume/status intents.
9. If user manually calls a subskill: resolve project root, then assert workflow route for that root first.
10. Whether routed from root Cadence or invoked directly, subskills run the same repo-status gate and finalize through `finalize-skill-checkpoint.py` with scope/checkpoint commit conventions.
11. For net-new ideation kickoff: after scaffold+prereq+project-mode-intake in-thread, force a fresh-chat handoff before running `ideator`.
12. For brownfield repositories: after intake, route to `brownfield-documenter` (not `ideator`) and force a new-chat handoff before documentation.
13. After ideator or brownfield-documenter completion, route to researcher and hand off into a dedicated researcher conversation (`Start a new chat with a new agent and say "research my project".`), then allow bounded multi-pass continuation in that same chat until context budget triggers handoff.
14. For greenfield flows, after researcher completion route to planner for roadmap planning (milestones/phases in initial planner scope).

Design emphasis:
- deterministic routing
- safety guardrails before state mutation
- user-facing output hygiene (hide internal traces unless requested)

### 3) Persist State
Canonical state file: `.cadence/cadence.json` (inside whichever project root Cadence is operating on).

Default model includes:
- `prerequisites-pass` (bool)
- `state.ideation-completed` (bool)
- `state.research-completed` (bool)
- `state.cadence-scripts-dir` (absolute helper script dir path)
- `state.repo-enabled` (bool; governs push vs local-only checkpoints)
- `state.project-mode` (`unknown|greenfield|brownfield`)
- `state.brownfield-intake-completed` (bool)
- `state.brownfield-documentation-completed` (bool)
- `planning` (greenfield roadmap object with milestone/phase detail in planner v1)
- `workflow.plan` (nested milestone -> phase -> wave -> task)
- `project-details.mode`, `project-details.brownfield_baseline`, and `ideation` objects
- `ideation.research_agenda` with normalized research `blocks`, `entity_registry`, and `topic_index` for later-phase deep research routing/querying
- `ideation.research_execution` with dynamic pass planning/queue, per-topic research status, pass history, and source registry

Current default actionable tasks:
- `task-scaffold` -> `scaffold`
- `task-prerequisite-gate` -> `prerequisite-gate`
- `task-brownfield-intake` -> `brownfield-intake`
- `task-brownfield-documentation` -> `brownfield-documenter`
- `task-ideation` -> `ideator`
- `task-research` -> `researcher`
- `task-roadmap-planning` -> `planner`

Mode-based task override:
- `greenfield` marks `task-brownfield-documentation` as `skipped`
- `brownfield` marks `task-ideation` as `skipped`
- non-greenfield modes mark `task-roadmap-planning` as `skipped`

### 4) Derive + Route Workflow
`workflow_state.py` is the core state engine:
- normalizes malformed/missing fields
- ensures ideation research agenda defaults exist in canonical shape
- coerces statuses (`pending|in_progress|complete|blocked|skipped`)
- rolls up parent statuses from children
- computes `workflow.summary`, `next_item`, `next_route`, completion percent
- maintains legacy compatibility fields (`next_phase`, `active_phase`, etc.)
- syncs legacy booleans from task status (`prerequisites-pass`, `ideation-completed`, `research-completed`, `brownfield-intake-completed`, `brownfield-documentation-completed`)
- applies project-mode-aware task status overrides for greenfield vs brownfield routing

`assert-workflow-route.py` blocks out-of-order state-changing subskill calls by checking requested skill against computed `next_route.skill_name`.

## Subskills (Functional Intent)
- `scaffold`: create `.cadence`, initialize `cadence.json`, persist scripts-dir, configure `.gitignore` track/ignore policy, initialize git/repo mode, checkpoint.
- `prerequisite-gate`: verify required Cadence runtime assets, persist prerequisite pass, checkpoint.
- `brownfield-intake`: classify project mode and persist deterministic baseline inventory for existing repositories before ideation routing.
- `brownfield-documenter`: investigate existing repo evidence deeply and persist canonical ideation + research agenda structures for brownfield projects.
- `ideator`: one-question-at-a-time project ideation, infer a complete domain-agnostic research agenda from the conversation, run an early exhaustive research-topic checkpoint (continue/add/remove) once concept and domain are clear, continue discovery, then run final pre-persistence topic review before persisting; treat execution planning as AI-driven by default (if timelines come up, estimate roughly 10-100x faster than human-only delivery without forcing timeline-specific prompts), then persist finalized ideation payload and checkpoint.
- `researcher`: execute ideation research agenda in dynamic, bounded multi-pass runs; persist findings to `cadence.json`; estimate context usage from token in/out totals, continue in-chat while under threshold, and hand off only when budget/cap requires a reset.
- `planner`: for greenfield projects, read Cadence ideation/research context and persist a semantic high-level roadmap (milestones/phases only in planner v1) into `cadence.json`.
- `ideation-updater`: discuss/modify existing ideation, keep research agenda synchronized, persist updated full ideation object, checkpoint.
- `project-progress`: read normalized workflow state, report progress (research-only metrics when route is `researcher`), route next action, checkpoint.
- `project-overview`: read-only utility subskill (manual invocation, not workflow-routed) that returns tabular project metadata and current position, and displays planner milestone/phase hierarchy when available (falling back to workflow milestone/phase/wave/task hierarchy).
- all subskills now include strict, skill-specific user-facing response templates to keep handoffs and completion output deterministic.

## Script System (Execution Backplane)
Key scripts by concern:

Workflow/state:
- `workflow_state.py`: normalization + derived workflow computation.
- `read-workflow-state.py`: load/reconcile/persist normalized state and emit route payload.
- `set-workflow-item-status.py`: set item status and recalculate all derived fields.
- `assert-workflow-route.py`: enforce legal skill transitions.
- `run-skill-entry-gate.py`: shared subskill preflight wrapper for root/scripts-dir/repo-status plus optional route/workflow checks.
- `resolve-project-root.py` + `project_root.py`: resolve active project root (cwd, explicit, or cached hint) so subskills can target the correct repo across chats.
- `query-json-fuzzy.py`: generic fuzzy JSON query helper used by supporting flows.
- `run-planner.py`: planner discovery (`discover`) and roadmap persistence (`complete`) for greenfield milestone/phase planning.

Scaffold/prereq:
- `scaffold-project.sh`: idempotent `.cadence` bootstrap (uses template fallback JSON).
- `run-scaffold-gate.py`: route assert + scaffold + scripts-dir init + state validation.
- `run-prerequisite-gate.py`: route assert + scripts-dir resolve + Cadence runtime-asset checks + state write.
- `run-brownfield-intake.py`: route assert + project mode classification + brownfield inventory baseline persistence.
- `run-brownfield-documentation.py`: route assert + helper discovery (`discover`) + explicit persistence (`complete`) of AI-authored ideation/research payload.
- `handle-prerequisite-state.py`: read/write `prerequisites-pass`.
- `resolve-project-scripts-dir.py` + `init-cadence-scripts-dir.py`: self-heal script path state.
- `configure-cadence-gitignore.py`: `.cadence` track/ignore policy updates.

Canonical invocation contracts (to avoid argument mismatch):
- `resolve-project-root.py`: always pass `--project-root "$PWD"` at entry so resolution is deterministic.
- `configure-cadence-gitignore.py`: accepts `--mode` and optional `--gitignore-path`; it does **not** accept `--project-root`.
- `finalize-skill-checkpoint.py`: accepts `--project-root`; pass it explicitly instead of relying on `cd` side effects.

Ideation:
- `ideation_research.py`: shared normalization and validation for ideation research agenda shape and entity/topic/block relationships.
- `prepare-ideation-research.py`: normalize and validate ideation payload research agenda before injection.
- `query-ideation-research.py`: granular query surface for `ideation.research_agenda` by block, topic, entity, category, tag, priority, and text.
- `run-research-pass.py`: dynamic pass planning and per-pass persistence for ideation research execution (start one pass, complete one pass, replan unresolved topics) with token-based in/out context estimation and threshold-driven handoff signaling.
- `run-project-overview.py`: read-only Cadence overview extraction for project metadata, current workflow position, workflow hierarchy, planner hierarchy, and planner-first display roadmap payloads.
- `inject-ideation.py`: validate/merge/replace ideation payload, enforce research agenda requirements when ideation is complete, route-guard when marking complete, optional payload-file deletion.
- `get-ideation.py`, `expose-ideation.py`, `render-ideation-summary.py`: machine/human ideation reads and summaries.

Git checkpoints:
- `check-project-repo-status.py`: detect git remote readiness (provider-agnostic by default); persist repo mode.
- `git-checkpoint.py`: stage paths, build conventioned commit message, commit, optional push.
- `finalize-skill-checkpoint.py`: split changed files into atomic semantic batches, call `git-checkpoint.py` per batch, honor local-only mode.

## Commit and Traceability Model
`skill/config/commit-conventions.json` defines:
- commit type: `cadence`
- subject max: 72 chars
- scopes/checkpoints (scaffold, prerequisite-gate, brownfield-intake, brownfield-documenter, ideator, researcher, planner, ideation-updater, project-progress, project-overview)
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
- apply this same finalization contract for both root-routed subskill runs and direct subskill invocations

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
- Repo history is release-driven (`v0.1.x` -> `v0.2.35`), with recent work focused on installer UX, brownfield routing/documentation, and safer workflow state handling.

## Practical Read of Maturity
What is strong:
- state normalization and backward-compatibility handling are explicit
- route guards reduce accidental phase skipping
- commit automation is unusually disciplined for AI workflows
- installer supports many AI tool ecosystems with one package

What is intentionally narrow right now:
- default workflow tracks Foundation setup, ideation research execution, and initial greenfield roadmap planning (scaffold/prereq/intake/brownfield-doc-or-ideation/research/planner)
- prerequisite gate currently validates required Cadence runtime assets only
- in-repo automated tests cover shared entry gate preflight behavior, repo status detection, workflow state transitions, route assertions, checkpoint batching, brownfield intake/documentation flows, and research-pass payload validation
- this repo ships framework/instructions; project-specific execution happens in downstream repos that install the skill

## Minimal Mental Model
Cadence = **workflow state machine + guarded skill router + atomic git checkpointer**, wrapped as a cross-tool installable skill package.

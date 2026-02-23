---
name: cadence
description: Structured project operating system for end-to-end greenfield or brownfield delivery. Use when users want the AI to guide the full lifecycle from initialization, requirements, roadmap, and phased execution through milestone audit and completion with deterministic gates, traceability, and rollback-safe execution.
---

# Cadence

## Overview
1. Keep this root skill as an orchestrator.
2. Delegate concrete execution to focused subskills.

## Scaffold Gate (Mandatory On First Turn)
1. Check for `.cadence` in the project root.
2. If `.cadence` is missing, invoke `skills/scaffold/SKILL.md`.
3. Scaffold initializes and persists `state.cadence-scripts-dir` for later subskill commands.
4. If `.cadence` exists, skip scaffold.

## Prerequisite Gate (Mandatory On First Turn)
1. Invoke `skills/prerequisite-gate/SKILL.md`.
2. Continue lifecycle and delivery execution only after prerequisite gate pass.

## Progress / Resume Flow
1. Invoke `skills/project-progress/SKILL.md` when the user asks to continue/resume or requests progress status (for example: "continue the project", "how far along are we?", "where did we leave off?").
2. Use that skill's state-based routing result to continue from the correct next phase.

## Ideation Flow
1. Do not switch to `skills/ideator/SKILL.md` inside this conversation.
2. After scaffold and prerequisite gates pass for a net-new project, hand off to a fresh chat so context resets cleanly.
3. Tell the user exactly: `now make a new chat and say "help me define my project" or provide a project brief.`
4. Stop here and wait for the user to continue in the new chat.

## Ideation Update Flow
1. If the user wants to modify or discuss existing ideation, invoke `skills/ideation-updater/SKILL.md`.
2. Use this update flow only for existing project ideation changes; use the new-chat handoff in Ideation Flow for net-new ideation discovery.

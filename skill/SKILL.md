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
3. If `.cadence` exists, skip scaffold.

## Prerequisite Gate (Mandatory On First Turn)
1. Invoke `skills/prerequisite-gate/SKILL.md`.
2. Continue lifecycle and delivery execution only after prerequisite gate pass.

## Ideation Flow
1. Invoke `skills/ideator/SKILL.md` when the user is creating, refining, or finalizing a project idea.
2. Continue downstream planning only after ideation is persisted in `.cadence/cadence.json`.

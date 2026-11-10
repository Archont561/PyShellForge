---
id: m-5
title: CI security and coverage
status: To Do
---

## Goal

Make the CI supply chain more predictable and report coverage across the supported
interpreter matrix.

## Outcome

GitHub Actions are pinned to commit SHAs and kept current. Linux matrix coverage
is combined into one gated report and uploaded to Codecov, with the workflow and
local commands documented.

## Dependencies

These tasks have no product-engine dependencies and can proceed independently of
the other milestones.

## Tasks

- `task-6`: Pin GitHub Actions to commit SHAs
- `task-7`: Aggregate coverage across the tox matrix in CI

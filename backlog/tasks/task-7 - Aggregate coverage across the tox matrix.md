---
id: task-7
title: Aggregate coverage across the tox matrix in CI
status: To Do
labels: [ci, coverage]
created_date: 2026-11-09
dependencies: []
references: [.github/workflows/ci.yml, tox.ini, .coveragerc]
---

## Description

Each compatibility cell writes `.tox/.coverage.py3XX`. Today the merged report is
produced locally (`tox -e coverage`) and in CI only for the single-version `full`
job, so a line reachable on 3.11 but not on 3.13 is invisible in the uploaded
report.

## Acceptance criteria

- [ ] Every Linux matrix cell uploads `.tox/.coverage.py3*` with
      `actions/upload-artifact`, named per interpreter.
- [ ] A `coverage` job downloads all artifacts, runs
      `coverage combine <dir>`, then `coverage report` and `coverage xml`.
- [ ] The job keeps the `fail_under = 90` gate and uploads `coverage.xml` to
      Codecov instead of the `full` job.
- [ ] `ci-result` requires the new job, and `docs/development/testing.md` says
      which job owns the report.

## Definition of done

- [ ] CI green, Codecov report shows merged data, `actionlint` passes.

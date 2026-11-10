---
id: decision-5
title: Bug reports arrive through YAML Issue Forms, validated offline
date: 2026-11-09
status: Accepted
references: [.github/ISSUE_TEMPLATE, automation/forms/check.py, automation/features/issue_forms.feature, docs/development/contributing.md]
---

## Context

A bug report for a code generator is only actionable with four facts: the version
of the package, the Python interpreter, the shell that ran the output, and the
smallest definition that reproduces the problem. A blank issue box collects none
of them, so the first reply is always a request for information, and the report
stalls.

GitHub offers two mechanisms. Markdown issue templates are a single text file with
front matter and a body of prose: easy to write, but they cannot require a field,
offer a dropdown or skip a question that does not apply. YAML Issue Forms define
typed elements (`input`, `textarea`, `dropdown`, `checkboxes`, `upload`,
`markdown`) with per-field validation, and GitHub renders them as a web form.

The catch is failure mode. GitHub accepts an Issue Form whose element type is
misspelled or whose `dropdown` has no `options`, then renders a form that loses
that field or refuses to open, and nothing in the repository notices. The schema
is only enforced at render time, in the browser, on GitHub.

## Decision

Ship YAML Issue Forms and check their schema offline with a repository script.

- `.github/ISSUE_TEMPLATE/bug_report.yml` asks for `psf version`, the Python
  version, the target shell, the affected area, a definition that reproduces the
  defect, the expected Bash and the actual Bash. Both required checkboxes confirm
  that the report is not a security issue, so a vulnerability never reaches a
  public tracker through this form.
- `.github/ISSUE_TEMPLATE/feature_request.yml` asks for the problem, the Python
  surface the contributor expects, the scope, the alternatives, and whether they
  will implement it.
- `.github/ISSUE_TEMPLATE/config.yml` disables blank issues and points at the
  documentation and the contributing guide, so the contact links stay inside the
  repository instead of becoming a second inbox.
- `python -m automation.forms` (`pixi run automation check-forms`) validates every template
  against the rules from GitHub's form schema that can be checked without the
  network: required keys, known element types, unique and well-formed ids, the
  attributes each type needs, `dropdown` options that are present and distinct,
  `default` and `multiple` shapes, `checkboxes` options, the validation keys each
  type accepts, and the `config.yml` contact links. Findings carry stable codes
  `PSF-FORM-001` to `PSF-FORM-017`, the path and the line of the element.
- The validator runs in `pixi run automation check`, in the pre-commit hook, in the CI
  documentation and policy job, and in the automation suite through its unit tests
  and its Gherkin scenarios. An edit under `.github/ISSUE_TEMPLATE/` counts as
  documentation scope in `automation/detect_changes.py`, so it does not trigger the
  interpreter and operating system matrix.
- Visual review stays manual: `gh form preview` from the
  [`gh-form`](https://github.com/yudai-nkt/gh-form) extension of the GitHub CLI
  renders a form locally. It needs `gh`, an authenticated session and network
  access, so it is a contributor step documented in the contributing guide, never
  a CI step.

## Consequences

- A contributor sees the fields a maintainer needs before submitting, and a
  mistyped element is caught in the pull request that introduces it.
- The repository keeps one kind of issue template. Markdown templates are gone,
  which also removes the ambiguity of a tracker with both.
- Pull request templates are out of scope: the form schema covers issues, and
  `gh form preview` confirms it does not render pull request templates.
- `pyyaml` is now a dependency of the documentation extra and of the Pixi
  environment, with `types-pyyaml` for the strict type check.
- The check cannot prove that GitHub renders the result the way a browser does.
  That gap is covered by the preview step, not by the validator, and the
  contributing guide says so.

## Alternatives considered

- **Markdown issue templates only.** Rejected: they cannot require a version or
  offer a shell dropdown, so they do not solve the problem that motivated the
  change, and they would have to be deleted before forms could be added.
- **YAML forms without a validator.** Rejected: the schema fails at render time in
  a browser, which is the one place this repository cannot test.
- **Render the forms in CI with `gh-form`.** Rejected: it needs an authenticated
  GitHub CLI and network access, which makes the gate non-deterministic. Offline
  schema validation covers the defects, and the preview stays a local step.
- **Add a third-party form generator or a hosted form service.** Rejected: issue
  templates belong to the repository, and a generator would add a dependency for
  a file of thirty lines.

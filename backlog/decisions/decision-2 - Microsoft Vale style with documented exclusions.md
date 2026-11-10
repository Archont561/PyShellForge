---
id: decision-2
title: Microsoft Vale style with three documented exclusions
date: 2026-11-09
status: Accepted
references: [.vale.ini, .vale/styles/README.md, docs/development/documentation.md]
---

## Context

Vale ran with the `Vale` style only, which caught spelling and terminology and
nothing else. The Archont561 repositories lint prose against the Microsoft style
package, so this repository followed, and the first run reported 138 errors and
30 warnings across 32 files.

Most findings were worth fixing: spaced em dashes (`word — word`), foreign-word
abbreviations (`e.g.`, `i.e.`), and inconsistent terminology. Three rule families
were not, and would have pushed the documentation away from its purpose.

## Decision

Vendor the Microsoft style package in `.vale/styles/Microsoft` and enable
`BasedOnStyles = Vale, Microsoft` for all Markdown, including `backlog/**`.
Disable exactly three rules in `.vale.ini`, each with the reason in a comment:

| Rule | Reason |
| --- | --- |
| `Microsoft.Contractions` | Reference documentation keeps a neutral, translation-friendly voice; expanding contractions is less ambiguous for readers whose first language is not English. |
| `Microsoft.Avoid` (`backend`) | The A-Z word list targets user-interface copy. `backend` is the domain term here and matches `pyshellforge.backends`. |
| `Microsoft.HeadingAcronyms` | Headings name API surface (`CLI`, `AST`, `PSF`); spelling the acronyms out would be less precise. |

Errors gate the check; warnings are advisory and are reviewed in the pull
request. Gherkin files are prose-shaped but structured, so `features/*.feature`
enforces spelling only.

## Consequences

- Prose now fails the build on has-dashes, foreign abbreviations, and terminology
  drift, which is what those rules are for.
- 17 warnings remain at baseline (`Microsoft.Adverbs`, one `Microsoft.Ellipses`);
  they are visible in every run instead of hidden, and each is a judgement call
  about a sentence that exists for a reason.
- The style package is vendored, so the check runs offline and in the sandbox;
  `pixi run automation update-prose-styles` refreshes it and the diff is reviewed like a
  dependency bump.
- New vocabulary goes in `.vale/styles/config/vocabularies/Project/accept.txt`,
  never into a disabled rule.

## Alternatives considered

- **Keep the `Vale` style only.** Rejected: it left 46 spaced dashes and every
  editorial rule uncaught.
- **Disable a rule per offending line.** Rejected: inline comments hide patterns
  and rot; a rule is either enforced or excluded with a global reason.
- **Fix the 17 warnings by rewriting the sentences.** Partially done (the dashes
  and the ellipsis are fixed); the rest are "deliberately" and "silently" where
  the adverb carries meaning.

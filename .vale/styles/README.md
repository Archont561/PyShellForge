# Vendored Vale styles

`Microsoft/` is a vendored copy of the
[Microsoft](https://github.com/errata-ai/Microsoft) style package from the Vale
registry. It is committed so that `pixi run lint-prose` works offline, in the
sandbox, and in CI without running `vale sync`.

## What is vendored

| Path | Source |
| --- | --- |
| `Microsoft/*.yml` | Microsoft style package (registry, pinned by `.vale.ini`) |
| `config/vocabularies/Project/accept.txt` | Project vocabulary (ours) |

## Refreshing the vendored copy

```sh
pixi run update-prose-styles   # vale sync, then review the diff
git diff .vale/styles/Microsoft
```

Two rules:

1. **Review the diff before committing.** A style bump can introduce new rules
   that fail the build; treat it like a dependency upgrade.
2. **Do not edit files under `Microsoft/` by hand.** Project-specific exceptions
   belong in `.vale.ini`, and project terms belong in
   `config/vocabularies/Project/accept.txt`.

## Why the Microsoft style

Microsoft's package encodes the editorial rules most technical documentation is
reviewed against: sentence shape, spacing around dashes, units and dates,
foreign-word expansion (`for example` instead of `e.g.`), and terminology
consistency. Without it, Vale only catches spelling.

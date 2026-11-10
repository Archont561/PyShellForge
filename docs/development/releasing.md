# Releasing to PyPI

The package is published by
[`.github/workflows/release.yml`](../../.github/workflows/release.yml), triggered
by pushing a version tag. Publishing uses
[PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/) (OIDC): no API
token is stored in this repository and no secret is read. The `pypi` GitHub
environment holds the trust registered on PyPI, and the publish job requests its
OIDC token from that environment.

The layout follows the sibling repository
[`Archont561/rude-clean-code`](https://github.com/Archont561/rude-clean-code): a
build job that checks the tag and the distributions, then a separate publish job
that only downloads the artifact and hands it to PyPI.

## What the workflow does

Two jobs, in order:

1. **Build and check distributions** (`build`): checks out the tag, sets up the
   locked Pixi environment, and runs `python -m automation.release`. That script
   - verifies that the tag (without its leading `v`) matches `[project].version`
     in `packages/pyshellforge/pyproject.toml`, and fails before building anything when it
     does not;
   - empties `dist/`, so a stale artifact cannot ride along into an upload;
   - builds the sdist and the wheel with `python -m build` (hatchling) and checks
     both with `twine check`;
   the distributions are then uploaded as the `distributions` workflow artifact.
   The build runs against the `packages/pyshellforge/` project directory and writes to
   `dist/` at the repository root, so nothing uploads a stale artifact.
2. **Publish to PyPI** (`publish`): downloads the artifact and publishes it with
   `pypa/gh-action-pypi-publish`, without checking out the repository. The job
   holds no repository permission, only `id-token: write` for the OIDC exchange,
   and it runs in the `pypi` environment, so any protection rule configured there
   applies before anything is uploaded.

`build` and `twine` are part of the locked Pixi environment
(`[pypi-dependencies]` in `pixi.toml`); nothing is installed ad hoc in the
workflow, and every `run:` step is a single line.

## Cutting a release

1. Bump `version` in `packages/pyshellforge/pyproject.toml` and commit the change. Version bumps are a
   maintainer action, and `CHANGELOG.md` gets the entry in the same commit.
2. Tag the commit with a `v`-prefixed tag that matches the version, then push it:

   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

3. The workflow builds and publishes. PyPI rejects a duplicate version, so a
   version is published once; a failed release is re-cut with a new version, never
   by re-tagging over a published one.

`VERSION` in the installed package comes from the same manifest, so the
value a user prints and the value PyPI accepted cannot disagree:

```bash
python -c "import pyshellforge; print(pyshellforge.VERSION)"
```

## Trying the build locally

```bash
pixi run automation check-release      # the tag/version guard only; writes nothing
pixi run automation release-build      # guard, clean dist/, build, twine check; uploads nothing
```

Outside CI there is no `GITHUB_REF_NAME`, so the guard reports that it was skipped
instead of failing, and `--ref v0.1.0` simulates the CI case:

```bash
python -m automation.release --ref v0.1.0 --check
```

`dist/` is generated output and is not committed.

## What is not automated

- **Tagging and version bumps are manual.** The workflow never creates a tag and
  never edits the manifest.
- **GitHub releases and changelog files** stay out of the release path;
  `CHANGELOG.md` is edited by hand under `Unreleased`.
- **The trusted publisher registration** lives on PyPI (project settings →
  publishing) and in the GitHub environment `pypi`. Changing it is a maintainer
  action outside this repository.

## How the release path is checked

`python -m automation.release` is covered by `automation/tests/test_release.py` and by
the `automation/features/release_build.feature` scenarios, `actionlint`
validates the
workflow, `alint` requires it to exist, and `pixi run automation check-release` runs the
version guard as part of `pixi run automation check` so a manifest without a static version
fails the gate rather than the release.

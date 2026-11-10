"""Regenerate ``README.md`` with readme-md-generator (npm).

The generator writes ``README.md`` into its *current working directory* and
prompts before overwriting an existing file. To stay non-interactive and
idempotent, this script renders inside a temporary directory that contains only
``package.json`` (the metadata the generator reads: name, version, description,
repository, author, license and ``engines`` prerequisites) and copies the result
back into the repository.

The template does not carry the banner either: it holds a marker, and
:func:`inject_banner` replaces that marker with FIGlet art rendered by
``automation.banner``. The freshness check therefore covers the banner as well,
so the page and the font data cannot drift apart.

Two files come out of the same template:

* ``README.md`` at the repository root, the page GitHub shows;
* ``packages/pyshellforge/README.md``, the distribution's long description. Hatchling
  refuses a readme outside the project directory, so PyPI needs its own copy.
  Its relative links are rebased (``docs/`` becomes ``../docs/``) so both copies
  resolve from where they sit.

Usage::

    python -m automation.readme            # rewrite both READMEs
    python -m automation.readme --check    # exit 1 when either file is stale (CI)

The generator version is pinned in ``package.json`` under ``devDependencies``.
Node.js is only needed for this script; the product, its tests and the other
repository automation is pure Python.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from automation.banner import WORDMARK, render_banner

#: Repository root, derived from this file (``automation/readme/generate.py``).
REPO_ROOT = Path(__file__).resolve().parents[2]

#: The ejs template that produces README.md.
TEMPLATE = Path(__file__).resolve().parent / "README.ejs"

#: Metadata file read by the generator.
PACKAGE_JSON = REPO_ROOT / "package.json"

#: Generated artefact: the repository landing page.
TARGET = REPO_ROOT / "README.md"

#: Generated artefact: the long description the package metadata points at.
PROJECT_TARGET = REPO_ROOT / "packages" / "pyshellforge" / "README.md"

#: Both files are rendered from the same template and must stay in sync.
TARGETS: tuple[Path, ...] = (TARGET, PROJECT_TARGET)

#: A markdown link with a relative target (external, mail and anchor links are
#: left alone because they do not depend on where the file lives).
RELATIVE_LINK = re.compile(r"\]\((?!(?:https?://|mailto:|#))([^)\s]+)\)")

#: npm package that provides the generator.
GENERATOR_PACKAGE = "readme-md-generator"

#: Marker the generator writes into every README it produces.
ATTRIBUTION = "This README was generated"

#: Where the template wants the wordmark. It is an HTML comment, so a marker that
#: ever survived into a page would be invisible rather than broken output.
BANNER_MARKER = "<!-- psf-banner -->"

#: A runner executes a command in ``cwd`` and returns its exit status.
Runner = Callable[..., int]


@dataclass(frozen=True)
class ReadmeResult:
    """Outcome of one generation run."""

    content: str
    command: tuple[str, ...]

    @property
    def attributed(self) -> bool:
        """Whether the output carries the generator's attribution footer."""
        return ATTRIBUTION in self.content


def subprocess_runner(command: Sequence[str], *, cwd: Path) -> int:
    """Run ``command`` in ``cwd`` with inherited stdio."""
    return subprocess.run(list(command), cwd=cwd, check=False).returncode


def pinned_version(package_json: Path = PACKAGE_JSON) -> str:
    """Return the exact generator version pinned in ``package.json``.

    Raises:
        ValueError: if the dependency is missing or not an exact pin.
    """
    data = json.loads(package_json.read_text(encoding="utf-8"))
    version = data.get("devDependencies", {}).get(GENERATOR_PACKAGE)
    if not version:
        msg = f"{GENERATOR_PACKAGE} is not pinned in {package_json.name}"
        raise ValueError(msg)
    if not all(part.isdigit() for part in str(version).split(".")):
        msg = f"pin {GENERATOR_PACKAGE} to an exact version, got {version!r}"
        raise ValueError(msg)
    return str(version)


def generator_command(version: str) -> list[str]:
    """Build the ``npx`` invocation used to run the pinned generator."""
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    return [npx, "--yes", f"{GENERATOR_PACKAGE}@{version}"]


def project_depth(target: Path) -> int:
    """Return how many directories separate ``target`` from the repository root."""
    try:
        return len(target.parent.resolve().relative_to(REPO_ROOT).parts)
    except ValueError:
        return 0


def inject_banner(content: str, *, art: str | None = None) -> str:
    """Replace every banner marker in ``content`` with the rendered wordmark.

    Args:
        content: the generated page.
        art: the art to insert; rendered from :data:`automation.banner.WORDMARK`
            when omitted, and injected by the tests to keep them font-independent.

    Returns:
        ``content`` with the markers replaced, or unchanged when it has none. A
        template without the marker is legitimate: the generator is also used on
        throwaway templates that only exercise the metadata.
    """
    if BANNER_MARKER not in content:
        return content
    rendered = render_banner(WORDMARK) if art is None else art
    return content.replace(BANNER_MARKER, rendered)


def relocate_links(content: str, depth: int) -> str:
    """Rebase relative markdown links for a copy that sits ``depth`` levels down."""
    if depth <= 0:
        return content
    prefix = "../" * depth
    return RELATIVE_LINK.sub(lambda match: f"]({prefix}{match.group(1)})", content)


def render_readme(
    *,
    template: Path = TEMPLATE,
    package_json: Path = PACKAGE_JSON,
    runner: Runner = subprocess_runner,
) -> ReadmeResult:
    """Render README content without touching the repository.

    Args:
        template: ejs template passed to the generator with ``-p``.
        package_json: metadata copied into the scratch directory.
        runner: callable executing the generator; injectable for tests.

    Raises:
        FileNotFoundError: if the template or ``package.json`` is missing.
        RuntimeError: if the generator fails or writes nothing.
    """
    if not template.is_file():
        msg = f"template not found: {template}"
        raise FileNotFoundError(msg)
    if not package_json.is_file():
        msg = f"metadata not found: {package_json}"
        raise FileNotFoundError(msg)

    command = [*generator_command(pinned_version(package_json)), "-y", "-p", str(template)]
    workdir = Path(tempfile.mkdtemp(prefix="psf-readme-"))
    try:
        shutil.copyfile(package_json, workdir / "package.json")
        status = runner(command, cwd=workdir)
        produced = workdir / "README.md"
        if status != 0:
            msg = f"{GENERATOR_PACKAGE} exited with status {status}"
            raise RuntimeError(msg)
        if not produced.is_file():
            msg = f"{GENERATOR_PACKAGE} did not produce a README.md"
            raise RuntimeError(msg)
        content = inject_banner(produced.read_text(encoding="utf-8"))
        return ReadmeResult(content=content, command=tuple(command))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def display_name(target: Path) -> str:
    """Return ``target`` relative to the repository root when it is inside it."""
    try:
        return target.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return target.name


def write_readme(
    *,
    check: bool = False,
    template: Path = TEMPLATE,
    package_json: Path = PACKAGE_JSON,
    targets: Sequence[Path] | None = None,
    runner: Runner = subprocess_runner,
) -> int:
    """Regenerate every ``targets`` file or verify they are current.

    Returns:
        0 on success, 1 when ``check`` finds a file stale or the generator
        fails, 2 when the template or metadata is missing.
    """
    destinations = tuple(targets) if targets is not None else TARGETS
    try:
        result = render_readme(template=template, package_json=package_json, runner=runner)
    except (FileNotFoundError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except RuntimeError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    if not result.attributed:
        print(f"error: generated output lacks the {GENERATOR_PACKAGE} attribution", file=sys.stderr)
        return 1

    status = 0
    for destination in destinations:
        content = relocate_links(result.content, project_depth(destination))
        name = display_name(destination)
        existing = destination.read_text(encoding="utf-8") if destination.is_file() else ""

        if check:
            if content != existing:
                print(
                    f"{name} is out of date.\n"
                    "Run `python -m automation.readme` and commit the result.",
                    file=sys.stderr,
                )
                status = 1
            else:
                print(f"{name} is up to date.")
        elif content == existing:
            print(f"{name} unchanged.")
        else:
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8")
            print(f"{name} written from {template.name}.")
    return status


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="python -m automation.readme",
        description="Regenerate README.md with readme-md-generator.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if README.md differs from a fresh generation",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=TEMPLATE,
        help="ejs template to render (default: the bundled README.ejs)",
    )
    args = parser.parse_args(argv)
    return write_readme(check=args.check, template=args.template)


if __name__ == "__main__":  # pragma: no cover - module entry point
    raise SystemExit(main())

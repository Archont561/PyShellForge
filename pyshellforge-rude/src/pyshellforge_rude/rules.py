"""Scope casing rules for PyShellForge definitions.

A PyShellForge definition is Python that becomes a shell script, and its two
scopes are not the same in the generated program: a binding at module level
becomes a global shell variable, while a binding inside a function becomes a
`local`. The shell cannot show that difference in a name, so the definition
has to.

The two rules are a pair. On its own, either one is a style preference; read
together they say that a name's case is how a reader sees its scope. Both run
only in files that mention PyShellForge or its `@sh` decorator, so installing
the plugin does not re-case every Python file in a repository.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import ClassVar

from rude import Diagnostic, FileContext, Node, NodeType, Rule, ScopeProvider, Severity
from rude.providers.semantic import SCOPE_FUNCTION, SCOPE_MODULE

#: A module-level name: optional leading underscores, then an upper-case letter.
#: `str.isupper` is not enough, because it is false for a name that has no cased
#: characters at all, and `MAX2` and `_TIMEOUT` are both legitimate.
MODULE_NAME = re.compile(r"_*[A-Z][A-Z0-9_]*")

#: Bindings a function body may create without a diagnostic.
EXEMPT_NAMES = frozenset({"self", "cls", "_"})

#: A definition is a file that mentions the package or its decorator.
MARKERS = ("pyshellforge", "@sh")


def is_definition(ctx: FileContext) -> bool:
    """Whether the file being checked uses PyShellForge."""
    return any(marker in ctx.text for marker in MARKERS)


def has_upper(name: str) -> bool:
    """Whether a name carries at least one upper-case letter."""
    return any(character.isupper() for character in name)


def target_of(node: Node) -> Node | None:
    """The identifier an assignment binds, when it binds a plain name.

    Attribute, subscript and tuple targets are not shell variables, so they are
    left to the compiler.
    """
    target = node.child_by_field("left")
    if target is None or target.type != NodeType.IDENTIFIER:
        return None
    return target


def name_of(parameter: Node) -> Node | None:
    """The identifier a parameter node declares.

    This grammar has no ``name`` field on a parameter, so the first identifier
    child is the name: `x`, `x=1` and `x: Int = 1` all put it there.
    """
    if parameter.type == NodeType.IDENTIFIER:
        return parameter
    for child in parameter.children:
        if child.type == NodeType.IDENTIFIER:
            return child
    return None


class ModuleGlobalsAreUpperCase(Rule):
    """PSF201 - a module-level binding becomes a global shell variable."""

    code: ClassVar[str] = "PSF201"
    message: ClassVar[str] = "module-level '{name}' becomes a script global; name it UPPER_CASE"
    node_types: ClassVar[set[NodeType] | None] = {NodeType.ASSIGNMENT}
    severity: ClassVar[Severity | None] = Severity.WARNING
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    def should_check_file(self, ctx: FileContext) -> bool:
        return is_definition(ctx)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        model = node.get_metadata(ScopeProvider).model
        if model is None:
            return
        if model.scope(model.scope_for(node)).type != SCOPE_MODULE:
            return
        target = target_of(node)
        if target is None or MODULE_NAME.fullmatch(target.text):
            return
        yield self.diagnostic(target, self.message.format(name=target.text))


class LocalsAreLowerCase(Rule):
    """PSF202 - a function-scoped binding becomes a `local` shell variable."""

    code: ClassVar[str] = "PSF202"
    message: ClassVar[str] = (
        "function-scoped '{name}' becomes a local shell variable; name it lower_case"
    )
    node_types: ClassVar[set[NodeType] | None] = {
        NodeType.ASSIGNMENT,
        NodeType.FUNCTION_DEFINITION,
    }
    severity: ClassVar[Severity | None] = Severity.WARNING
    metadata_dependencies: ClassVar[set[type]] = {ScopeProvider}

    def should_check_file(self, ctx: FileContext) -> bool:
        return is_definition(ctx)

    def check(self, node: Node) -> Iterator[Diagnostic]:
        if node.type == NodeType.FUNCTION_DEFINITION:
            yield from self._parameters(node)
        else:
            yield from self._assignment(node)

    def _parameters(self, node: Node) -> Iterator[Diagnostic]:
        for parameter in node.parameters:
            name = name_of(parameter)
            if name is not None:
                yield from self._report(name)

    def _assignment(self, node: Node) -> Iterator[Diagnostic]:
        model = node.get_metadata(ScopeProvider).model
        if model is None:
            return
        scope = model.scope(model.scope_for(node))
        if scope.type != SCOPE_FUNCTION:
            return
        target = target_of(node)
        # `global` and `nonlocal` rebind an outer name, so the casing decision
        # belongs to the scope that declares it.
        if target is None or target.text in scope.globals or target.text in scope.nonlocals:
            return
        yield from self._report(target)

    def _report(self, name: Node) -> Iterator[Diagnostic]:
        if name.text in EXEMPT_NAMES or not has_upper(name.text):
            return
        yield self.diagnostic(name, self.message.format(name=name.text))

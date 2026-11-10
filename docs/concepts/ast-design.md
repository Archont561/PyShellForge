# AST design

A script is a sequence of shell-neutral `Node` objects held by `ShellScript`.
The container passes an immutable snapshot to a renderer, which decides how to
express each node for its target. `BashRenderer` is the first renderer; no other
shell target is implemented yet.

The first nodes are `Comment`, `VariableAssignment`, `Command` and `Echo`. A
`Command` holds a command name and literal arguments, not a raw shell fragment.
The renderer quotes those literals centrally. `Echo` holds a template string:
`{NAME}` means a previously declared variable and doubled braces mean literal
braces. The renderer escapes literal text inside the generated double quotes.
`{NAME!q}` requests Bash runtime quoting; other conversions and format specs are
rejected. A Python f-string must not be used as the template, because Python
would evaluate it before the renderer could check it.

A renderer raises `UnsupportedNodeError` with the node and target when it cannot
render a node. The current Bash renderer tracks declarations in order and raises
`InterpolationError` for an undeclared or malformed name. No shell code or
Python expression is evaluated while rendering. Validation, control flow, and a
public plugin registry are planned separately.

Back to the [documentation index](../README.md).

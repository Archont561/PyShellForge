# API reference

The public Python API currently renders a small subset of Bash. It does not yet
include a CLI, validation engine or additional shell backends.

```python
from pyshellforge import Command, Comment, Echo, ShellScript, VariableAssignment

script = ShellScript().add(
    Comment("A greeting"),
    VariableAssignment("NAME", "Ada Lovelace"),
    Echo("Hello {NAME}"),
    Command("printf", ("%s\\n", "done")),
)
print(script.render())
```

`ShellScript(renderer=None)` defaults to `BashRenderer`. `add(*nodes)` appends
nodes in order and returns the script. `render()` returns a complete script with
a Bash shebang and a final newline. A supplied renderer implements
`render(nodes)` and receives a snapshot of the node sequence.

## Nodes

- `Comment(text)` renders one comment per line, removing trailing whitespace.
  NUL and carriage returns are rejected.
- `VariableAssignment(name, value)` assigns a literal string. Names must match
  `[A-Za-z_][A-Za-z0-9_]*`; a value containing NUL is rejected.
- `Command(name, args=())` emits a command and literal string arguments. It does
  not accept raw shell syntax, redirections or expansions as arguments.
- `Echo(template)` prints exactly one line using `printf '%s\n'`. Use a normal
  string containing `{NAME}` to expand a variable assigned earlier. `{{` and
  `}}` are literal braces. `{NAME!q}` applies Bash `printf %q` at runtime.
  Literal dollar signs, quotes, backslashes and backticks are escaped. NUL and
  line breaks in a template are rejected.

`InterpolationError` reports invalid or undeclared names, malformed templates,
format specs and unsupported conversions. `UnsupportedNodeError` names the node
and the target for nodes the selected renderer does not support. These errors
occur during rendering; no template is evaluated as Python.

Back to the [documentation index](../README.md).

<!--
  Generated file - do not edit README.md by hand.

  Source template : automation/readme/README.ejs
  Generator       : readme-md-generator (pinned in package.json)
  Regenerate with : pixi run automation readme   (python -m automation.readme)
  Verify in CI    : pixi run automation readme-check
-->

<h1 align="center">PyShellForge</h1>

<pre style="font-family: monospace">
██████╗ ██╗   ██╗███████╗██╗  ██╗███████╗██╗     ██╗     ███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔══██╗╚██╗ ██╔╝██╔════╝██║  ██║██╔════╝██║     ██║     ██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
██████╔╝ ╚████╔╝ ███████╗███████║█████╗  ██║     ██║     █████╗  ██║   ██║██████╔╝██║  ███╗█████╗
██╔═══╝   ╚██╔╝  ╚════██║██╔══██║██╔══╝  ██║     ██║     ██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝
██║        ██║   ███████║██║  ██║███████╗███████╗███████╗██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝        ╚═╝   ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝</pre>

<p>
  <img alt="Version: 0.1.0" src="https://img.shields.io/badge/version-0.1.0-blue.svg?cacheSeconds=2592000" />
  <a href="https://github.com/Archont561/pyshellforge/blob/main/docs/README.md" target="_blank">
    <img alt="Documentation" src="https://img.shields.io/badge/documentation-yes-brightgreen.svg" />
  </a>
  <img alt="python 3.11+" src="https://img.shields.io/badge/python-%3E%3D3.11-blue.svg" />
  <a href="https://codecov.io/gh/Archont561/pyshellforge" target="_blank">
    <img alt="Coverage" src="https://img.shields.io/codecov/c/github/Archont561/pyshellforge.svg" />
  </a>
  <a href="https://github.com/Archont561/pyshellforge/blob/main/LICENSE" target="_blank">
    <img alt="License: MIT" src="https://img.shields.io/github/license/Archont561/pyshellforge" />
  </a>
</p>

> Write shell scripts in Python. Render clean Bash.
>
> A Python-native DSL for building, composing and rendering structured Bash
> scripts. The package is a skeleton: it exposes `VERSION` and nothing else, and
> the renderer is planned work.

### 🏠 [Homepage](https://github.com/Archont561/PyShellForge#readme)

## Documentation

The [`docs/`](../docs/README.md) directory is the source of truth for using and
working on this repository:

- [Documentation index](../docs/README.md): everything, organized by purpose
- [Install](../docs/guides/install.md): prerequisites, installation, the locked developer sandbox
- [Repository layout](../docs/reference/repository-layout.md): what lives where and why
- [Linting](../docs/reference/linting.md): the Rude plugin, its rule codes, and the rules that wait for the validator
- [Project status](../docs/concepts/version-only-scaffold.md): what exists today and what the roadmap adds
- [Contributing](../docs/development/contributing.md): setup, the checks CI runs, the commit and merge policy
- [Testing](../docs/development/testing.md): test layout, what each layer proves, coverage
- [Tooling](../docs/development/tooling.md): the `automation` CLI, its task graph, hooks and linters
- [Documentation](../docs/development/documentation.md): policy, structure, validation and definition of done
- [Releasing](../docs/development/releasing.md): the tag-triggered release and trusted publishing

Planned work is tracked in [`backlog/`](../backlog/), and the release history is
[`CHANGELOG.md`](../CHANGELOG.md).

## Install

```sh
pip install pyshellforge
```

## Usage

```sh
python -c "import pyshellforge; print(pyshellforge.VERSION)"
```

## Run tests

```sh
pixi run automation test-all
```

## Author

👤 **PyShellForge contributors**

- Website: [archont561.github.io/Archont561](https://archont561.github.io/Archont561/)
- GitHub: [@Archont561](https://github.com/Archont561)

## 🤝 Contributing

Contributions, issues and feature requests are welcome!<br />Feel free to check
the [issues page](https://github.com/Archont561/PyShellForge/issues). You can also take a look at the
[contributing guide](../CONTRIBUTING.md): it covers setup, the checks a change has
to pass and the merge policy.

## Show your support

Give a ⭐️ if this project helped you!

## 📝 License

Copyright © 2026 [PyShellForge contributors](https://github.com/Archont561).<br />
This project is [MIT](https://github.com/Archont561/pyshellforge/blob/main/LICENSE) licensed.

***

*This README was generated with ❤️ by [readme-md-generator](https://github.com/kefranabg/readme-md-generator) from [`automation/readme/README.ejs`](../automation/readme/README.ejs).*

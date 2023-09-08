# Creating a great Python DevX
> Create an enjoyable and meaningful Python Developer eXperience._

I have recently created a trivial open source Python package, named [`tally-counter`](https://github.com/houseman/tally-counter). The objective here was to play around with some tooling that can make producing Python projects easier and better, rather than the product itself.

> "The journey is the thing."
>
> -- Homer

Let me take you through it.

## Tooling
> **Important**
> The scope of this post is not to give the reader instruction on how to configure and these tools. SOme tips are given, and excellent  documentation is available at the links provided.

### Nox
[Nox](https://github.com/wntrblm/nox) is a command-line tool that automates testing in multiple Python environments.

**Why use this?** An open source Python package should support all current Python versions (currently `>= 3.9, <= 3.11`). Nox can run unit tests and linting fixes or checks in all of these Python versions in a single execution.

Here is my `noxfile.py` (kind of cool that the configuration language is Python):
```python
"""Nox configuration."""
import enum
import os

import nox

# Set to True if Nox is running in CI (GitHub Actions)
CI = os.environ.get("CI") is not None

# Supported Python versions
PYTHON_VERSIONS = ["3.8", "3.9", "3.10", "3.11"]


class Tag(str, enum.Enum):
    """Define acceptable tag values."""

    TEST = "test"
    LINT = "lint"


@nox.session(python=PYTHON_VERSIONS, tags=[Tag.TEST])
def pytest(session):
    """Run all unit tests."""
    ...  # Snipped


@nox.session(python=PYTHON_VERSIONS, tags=[Tag.TEST])
def doctest(session):
    """Run doc tests."""
    ...  # Snipped


@nox.session(python=PYTHON_VERSIONS, tags=[Tag.LINT])
def black(session):
    """Run the black formatter."""
    ...  # Snipped


@nox.session(python=PYTHON_VERSIONS, tags=[Tag.LINT])
def ruff(session):
    """Run the ruff linter."""
    ...  # Snipped


@nox.session(python=PYTHON_VERSIONS, tags=[Tag.LINT])
def mypy(session):
    """Run the mypy type checker."""
    ...  # Snipped
```

> **Note**
> Specifying session `tags=[...]` parameters enables grouping of sessions by purpose.

### Ruff
[Ruff](https://github.com/astral-sh/ruff) is an extremely fast Python linter, written in Rust.

**Why use this?** Linting is a great way to detect buggy or poorly-implemented (smelly) code.
Ruff is able to lint code to a number of well-defined style rules.

Here is an extract of rules to follow from the `pyproject.toml` file:
```toml
[tool.ruff]
select = [
  "E",  # pycodestyle Error
  "F",  # Pyflakes
  "B",  # flake8-bugbear
  "W",  # pycodestyle Warning
  "I",  # isort
  "N",  # pep8-naming
  "D",  # pydocstyle
  "PL", # Pylint
]
ignore = [
  "D107", # Missing docstring in `__init__`
  "D203", # 1 blank line required before class docstring
  "D212", # Multi-line docstring summary should start at the first line
]
```

> Ruff [editor integrations](https://beta.ruff.rs/docs/editor-integrations/) are available.

### Mypy
[Mypy](https://github.com/python/mypy) is a static type checker for Python.

**Why use this?** Checked Python type annotations make code safer and easier to read and understand.

### Black
[Black](https://github.com/psf/black) is the uncompromising Python code formatter.

**Why use this?** When code is shared in a team or community environment, it makes sense to have this code conform to a standard format. This removes ambiguity and allows contributors to focus on implementation. Formatted code is also less prone to raising linting issues.

### pre-commit
[pre-commit](https://github.com/pre-commit/pre-commit) runs a number of checks before git commits may succeed.

**Why use this?** Running pre-commit checks save committing incomplete or faulty code by detecting issues before the commit may succeed. Some of these are just downright useful:
- configuration file (*.yaml, *.toml) file formatting
- newlines at the end of file
- merge conflict markers
- unit test function names
- committing to "main" branch
- etc., etc., etc.

### make
I have also created a `Makefile` that contains some helpful shortcuts for often-used instructions.
```shell
❯ make help
help                 Show this help message
install              Install dependencies
lint                 Run linting in all supported Python versions
test                 Run unit tests in all supported Python versions
update               Update dependencies
```

The `lint` and `test` targets use Nox to run these jobs on all supported Python versions (>= 3.8, <= 3.11).
This does take a bit longer, and requires that the supported Python versions are installed on the developer's machine.
(One that note, have a look at [`pyenv`](https://github.com/pyenv/pyenv)).

You can thus specify which Python version(s) should be used by Nox like this:
```shell
make lint PYTHON_VERSIONS="3.8"
```

## Continuous Integration and Delivery
The project makes use of GitHub Actions to facilitate Ci/CD workflow.

When it comes to release workflows, there is no _one size fits all_ solution. Requirements will vary based on the project's maturity and the number of contributors. And requirements will change as the project grows.

For this project, I have decided on the following flow.
1. Create a new feature branch from `main`
2. Branch off, and merge into, this branch as required
   - Each push is checked for a [semantic version](https://semver.org/) increment (or "bump")
   - Linting checks
   - Unit tests
3. When ready, create a pull request to merge the feature branch to "main"
4. Once the pull request is approved, the branch should be squashed and merged to "main"
   - Create a new release named for the semantic version
   - Publish this version to PyPI

### Build
The [Build Action](https://github.com/houseman/tally-counter/blob/main/.github/workflows/build.yml) runs these steps:
- check that the branch's semantic version has been bumped, in `pyproject.toml`
- run linting checks on Ubuntu, MacOS and Windows operating systems, for all supported Python versions
- run unit test on Ubuntu, MacOS and Windows operating systems, for all supported Python versions
- if the branch is `main`, create a new GitHub release, named for the semantic version

#### Semantic version check
This was a bit of a hack, but works. At the moment, I cannot think of a better way.

The package `__init__.py` contains this code to set a `__version__` variable:
```python
"""Tally Counter."""
import importlib.metadata

# ... snipped ...
__version__ = importlib.metadata.version("tally_counter")

```
This string values can then be accessed by:
```python
>>> import tally_counter
>>> tally_counter.__version__
'0.0.9'
```
The build CI can then map this output to a `BRANCH_VERSION` environment variable:
```yaml
# ... snipped ..
jobs:
  get-branch-version:
    runs-on: ubuntu-latest
    # Map BRANCH_VERSION as an output of this step
    outputs:
      BRANCH_VERSION: ${{ steps.branch-version.outputs.BRANCH_VERSION }}
    steps:
      # ... snipped ..
      - name: Install this package
        run: |
          python -m pip install --upgrade pip
          pip install .
      - name: Set BRANCH_VERSION
        id: branch-version
        run: echo "BRANCH_VERSION=$(python -c 'import tally_counter; print(tally_counter.__version__)')" >> "$GITHUB_OUTPUT"
# ... snipped ..
```
And then checkout `main`, and do the same again
```yaml
jobs:
  # ... snipped ..
  version-check:
    runs-on: ubuntu-latest
    needs: get-branch-version
    if: ${{ github.ref != 'refs/heads/main' }} # Skip if this push is to "main"
    steps:
      # ... snipped ..
      - name: Checkout main branch
        run: |
          git fetch origin main:main
          git checkout main
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install semver
          pip install .
      - name: Set MAIN_VERSION
        id: get-main-version
        run: echo "MAIN_VERSION=$(python -c 'import tally_counter; print(tally_counter.__version__)')" >> "$GITHUB_OUTPUT"
      - name: Compare BRANCH_VERSION > MAIN_VERSION
        env:
          MAIN_VERSION: ${{ steps.get-main-version.outputs.MAIN_VERSION }} # From step above
          BRANCH_VERSION: ${{ needs.get-branch-version.outputs.BRANCH_VERSION }} # From get-branch-version job output
        run: python -c "import semver; assert semver.compare('${{ env.BRANCH_VERSION }}', '${{ env.MAIN_VERSION }}') > 0, 'Version not bumped'"
# ... snipped ..
```

### Publish
A [second action](https://github.com/houseman/tally-counter/blob/main/.github/workflows/publish.yml) will publish the new version to PyPI


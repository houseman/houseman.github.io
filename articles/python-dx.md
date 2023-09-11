# Creating a great Python DevX
> _Create an enjoyable and meaningful Python Developer eXperience._

I have recently created a trivial open source Python package, named [`tally-counter`](https://github.com/houseman/tally-counter).
The objective here was to play around with some tooling that could make shipping Python projects easier and better, rather than the product itself.

> "The journey is the thing."
>
> -- Homer

Let me take you through it.

## Tooling
> **Important**
> The scope of this post is not to give the reader instruction on how to configure and implement these tools. Some tips are given, and excellent  documentation is available at the links provided.

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
[View source](https://github.com/houseman/tally-counter/blob/main/noxfile.py)

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
[View source](https://github.com/houseman/tally-counter/blob/main/pyproject.toml)

> Ruff [editor integrations](https://beta.ruff.rs/docs/editor-integrations/) are available.

### Mypy
[Mypy](https://github.com/python/mypy) is a static type checker for Python.

**Why use this?** Checked Python type annotations make code safer and easier to read and understand.

> A NyPy [Visual Studio Code extension](https://marketplace.visualstudio.com/items?itemName=ms-python.mypy-type-checker) is available.

### Black
[Black](https://github.com/psf/black) is the uncompromising Python code formatter.

**Why use this?** When code is shared in a team or community environment, it makes sense to have this code conform to a standard format. This removes ambiguity and allows contributors to focus on implementation. Formatted code is also less prone to raising linting issues.

> Black [editor integrations](https://black.readthedocs.io/en/stable/integrations/editors.html) are available.

### pre-commit
[pre-commit](https://github.com/pre-commit/pre-commit) runs a number of checks before git commits may succeed.

**Why use this?** Running pre-commit checks may prevent committing incomplete or faulty code by detecting issues before the commit may succeed. Some of these are just downright useful:
- configuration file (`*.yaml`, `*.toml`) formatting
- newlines at the end of file
- merge conflict markers
- unit test function names
- committing to `main` branch
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
This does take a bit longer, and requires that the supported Python versions are installed on the developer's machine (on that note, do have a look at [`pyenv`](https://github.com/pyenv/pyenv)).

You can thus specify which Python version(s) should be used by Nox like this:
```shell
make lint PYTHON_VERSIONS="3.8"
```

## Continuous Integration and Delivery
The project makes use of GitHub Actions to facilitate Ci/CD workflow.

When it comes to release workflows, there is no _one size fits all_ solution. Requirements will vary based on the project's maturity and the number of contributors. And requirements will change as the project grows.

For this project, I have decided on the typical [Git Feature Branch Workflow](https://www.atlassian.com/git/tutorials/comparing-workflows/feature-branch-workflow).
1. Create a new feature branch off `main`
2. Branch further off - and merge back into - this feature branch as required. The Build action runs for each push:
   - If the current branch is off `main`, then
     - check for a [semantic version](https://semver.org/) increment (or "bump")
   - Run all linting checks
   - Run all unit tests
3. When ready, create a pull request to merge the feature branch to `main`
4. Once the pull request is approved, the branch should be squashed and merged to `main`
   - The **Build** action runs
   - if the branch is `main`, then
     - Create a new release named for the semantic version
     - Create a Python package build
     - Publish this version to PyPI

### Build
The [Build Action](https://github.com/houseman/tally-counter/blob/main/.github/workflows/ci-build.yml) runs these steps:
- check that the branch's semantic version has been bumped, in `pyproject.toml`
- run linting checks on Ubuntu, MacOS and Windows operating systems, for all supported Python versions
- run unit test on Ubuntu, MacOS and Windows operating systems, for all supported Python versions
- if the branch is `main`, create a new GitHub release, named for the semantic version

#### Semantic version check
This was a bit of a hack, but it works quite well. At the moment, I cannot think of a better way.

The`pyproject.toml` `project.version` attribute is our single source of truth for the package sematic version.
```toml
[project]
name = "tally-counter"
version = "0.0.9"
```

To create a mechanism of retrieving this, the package `__init__.py` contains this code to set a `__version__` variable:
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
  # Get the HEAD branch semantic version
  head-branch-version:
    runs-on: ubuntu-latest
    # Map outputs to environment variables
    outputs:
      HEAD_VERSION: ${{ steps.set-head-version.outputs.HEAD_VERSION }}
      HEAD_OFF_MAIN: ${{ steps.set-head-off-main.outputs.HEAD_OFF_MAIN }}
    steps:
      # ... snipped ..
      - name: Pip install this package
        run: |
          python -m pip install --upgrade pip
          pip install .
      - name: Set HEAD_VERSION
        id: set-head-version
        run: echo "HEAD_VERSION=$(python -c 'import tally_counter; print(tally_counter.__version__)')" >> "$GITHUB_OUTPUT"
      - name: Set HEAD_OFF_MAIN
        id: set-head-off-main
        if: ${{ github.ref != 'refs/heads/main' }} # Skip if "main"
        run: |
          git fetch origin main:main
          if git merge-base --is-ancestor main HEAD; then
            echo "HEAD_OFF_MAIN=1" >> "$GITHUB_OUTPUT"
          else
            echo "HEAD_OFF_MAIN=0" >> "$GITHUB_OUTPUT"
          fi
# ... snipped ..
```
And then checkout `main`, and do the same again
```yaml
# ... snipped ..
jobs:
  # ... snipped ..
  version-check:
    runs-on: ubuntu-latest
    needs: head-branch-version
    # Run a semantic version check if this push is to a main descendant
    if: ${{ needs.head-branch-version.outputs.HEAD_OFF_MAIN == '1' }}
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
        id: set-main-version
        run: echo "MAIN_VERSION=$(python -c 'import tally_counter; print(tally_counter.__version__)')" >> "$GITHUB_OUTPUT"
      - name: Compare HEAD_VERSION > MAIN_VERSION
        env:
          MAIN_VERSION: ${{ steps.set-main-version.outputs.MAIN_VERSION }}
          HEAD_VERSION: ${{ needs.head-branch-version.outputs.HEAD_VERSION }}
        run: python -c "import semver; assert semver.compare('${{ env.HEAD_VERSION }}', '${{ env.MAIN_VERSION }}') > 0, 'Version not bumped'"
# ... snipped ..
```
Once all checks have passed, a release is built.
```yaml
# ... snipped ..
  # Create a new release if branch is "main"
  release:
    needs: [head-branch-version, build]
    runs-on: ubuntu-latest
    if: ${{ github.ref == 'refs/heads/main' }} # Only create a release if the push branch is "main"
    steps:
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HEAD_VERSION: ${{ needs.head-branch-version.outputs.HEAD_VERSION }}
        with:
          tag_name: "v${{ env.HEAD_VERSION }}"
          release_name: "v${{ env.HEAD_VERSION }}"
          draft: false
          prerelease: false
```
### Publish
A [second action](https://github.com/houseman/tally-counter/blob/main/.github/workflows/ci-publish.yml) will publish the new version to PyPI

## Conclusion

This was just a quick and very high-level overview of the process. It can almost certainly be improved upon.
Have a look at the https://github.com/houseman/tally-counter repository to gain further insight on how it all fits together.

Cheers!
#!/usr/bin/env python3
"""Ensure __version__ is in sync with the package metadata."""

import re
import sys
from pathlib import Path

import toml


def main():
    metadata = toml.load("pyproject.toml")["tool"]["poetry"]
    version = metadata["version"]
    name = metadata["name"]

    init_py_path = Path("src", name, "__init__.py")
    with open(init_py_path, "r") as f:
        content = f.read()

    matches = list(re.finditer(r'^__version__ = [\'"]([^\'"]*)[\'"]$', content))
    assert len(matches) == 1
    start, end = matches[0].span(1)
    content = content[:start] + version + content[end:]

    with open(init_py_path, "w") as f:
        f.write(content)


if __name__ == "__main__":
    sys.exit(main())

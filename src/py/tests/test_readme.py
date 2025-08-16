"""Tests for validating code examples in the project documentation.

This file is part of the tschm/.config-templates repository
(https://github.com/tschm/.config-templates).


This module contains tests that extract Python code blocks from the README.md file
and run them through doctest to ensure they are valid and working as expected.
This helps maintain accurate and working examples in the documentation.
"""

import doctest
import os
import re
import warnings
from pathlib import Path

import pytest
from _pytest.capture import CaptureFixture


def find_project_root(start_path: Path = None) -> Path:
    """Find the project root directory by looking for the .git folder.

    This function iterates up the directory tree from the given starting path
    until it finds a directory containing a .git folder, which is assumed to be
    the project root.

    Args:
        start_path (Path, optional): The path to start searching from.
            If None, uses the directory of the file calling this function.

    Returns:
        Path: The path to the project root directory.

    Raises:
        FileNotFoundError: If no .git directory is found in any parent directory.
    """
    if start_path is None:
        # If no start_path is provided, use the current file's directory
        start_path = Path(__file__).parent

    # Convert to absolute path to handle relative paths
    current_path = start_path.absolute()

    # Iterate up the directory tree
    while current_path != current_path.parent:  # Stop at the root directory
        # Check if .git directory exists
        git_dir = current_path / ".git"
        if git_dir.exists() and git_dir.is_dir():
            return current_path

        # Move up to the parent directory
        current_path = current_path.parent

    # If we've reached the root directory without finding .git
    raise FileNotFoundError("Could not find project root: no .git directory found in any parent directory")


@pytest.fixture
def project_root() -> Path:
    """Fixture that provides the project root directory.

    Returns:
        Path: The path to the project root directory.
    """
    return find_project_root(Path(__file__).parent)


@pytest.fixture()
def docstring(project_root: Path) -> str:
    """Extract Python code blocks from README.md and prepare them for doctest.

    This fixture reads the README.md file, extracts all Python code blocks
    (enclosed in triple backticks with 'python' language identifier), and
    combines them into a single docstring that can be processed by doctest.

    Args:
        project_root: Path to the project root directory

    Returns:
        str: A docstring containing all Python code examples from README.md

    """
    # Read the README.md file
    try:
        with open(project_root / "README.md", encoding="utf-8") as f:
            content = f.read()

            # Extract Python code blocks (assuming they are in triple backticks)
            blocks = re.findall(r"```python(.*?)```", content, re.DOTALL)

            code = "\n".join(blocks).strip()

            # Add a docstring wrapper for doctest to process the code
            docstring = f"\n{code}\n"

            return docstring

    except FileNotFoundError:
        warnings.warn("README.md file not found")
        return ""


def test_blocks(project_root: Path, docstring: str, capfd: CaptureFixture[str]) -> None:
    """Test that all Python code blocks in README.md execute without errors.

    This test runs all the Python code examples from the README.md file
    through doctest to ensure they execute correctly. It captures any
    output or errors and fails the test if any issues are detected.

    Args:
        project_root: Path to the project root directory
        docstring: String containing all Python code examples from README.md
        capfd: Pytest fixture for capturing stdout/stderr output

    Raises:
        pytest.fail: If any doctest fails or produces unexpected output

    """
    # Change to the root directory to ensure imports work correctly
    os.chdir(project_root)

    try:
        # Run the code examples through doctest
        doctest.run_docstring_examples(docstring, globals())
    except doctest.DocTestFailure as e:
        # If a DocTestFailure occurs, capture it and manually fail the test
        pytest.fail(f"Doctests failed: {e}")

    # Capture the output after running doctests
    captured = capfd.readouterr()

    # If there is any output (error message), fail the test
    if captured.out:
        pytest.fail(f"Doctests failed with the following output:\n{captured.out} and \n{docstring}")

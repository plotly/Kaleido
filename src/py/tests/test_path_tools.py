from pathlib import Path

import pytest

from kaleido import _path_tools


def test_next_filename_no_existing_files(tmp_path):
    """Test _next_filename when no files exist."""
    result = _path_tools._next_filename(tmp_path, "test", "png")  # noqa: SLF001
    assert result == "test.png"


def test_next_filename_base_file_exists(tmp_path):
    """Test _next_filename when base file exists."""
    # Create the base file
    (tmp_path / "test.png").touch()

    result = _path_tools._next_filename(tmp_path, "test", "png")  # noqa: SLF001
    assert result == "test-2.png"


def test_next_filename_numbered_files_exist(tmp_path):
    """Test _next_filename when numbered files exist."""
    # Create various numbered files
    (tmp_path / "test.png").touch()
    (tmp_path / "test-2.png").touch()
    (tmp_path / "test-3.png").touch()
    (tmp_path / "test-5.png").touch()  # Gap in numbering

    result = _path_tools._next_filename(tmp_path, "test", "png")  # noqa: SLF001
    assert result == "test-6.png"  # Should be max + 1


def test_next_filename_similar_names_ignored(tmp_path):
    """Test _next_filename ignores files with similar but different names."""
    # Create files that shouldn't match the pattern
    (tmp_path / "test.png").touch()
    (tmp_path / "test-2.png").touch()
    (tmp_path / "testing-3.png").touch()  # Different prefix
    (tmp_path / "test-2.jpg").touch()  # Different extension
    (tmp_path / "test-abc.png").touch()  # Non-numeric suffix

    result = _path_tools._next_filename(tmp_path, "test", "png")  # noqa: SLF001
    assert result == "test-3.png"  # Should only count test.png and test-2.png


def test_next_filename_special_characters(tmp_path):
    """Test _next_filename with special characters in prefix and extension."""
    prefix = "test-?f$ile_name"
    ext = "s$v&*g"  # set up to be parameterized but not

    # Create some files
    (tmp_path / f"{prefix}.{ext}").touch()
    (tmp_path / f"{prefix}-2.{ext}").touch()

    result = _path_tools._next_filename(tmp_path, prefix, ext)  # noqa: SLF001
    assert result == f"{prefix}-3.{ext}"


def test_next_filename_only_numbered_files(tmp_path):
    """Test _next_filename when only numbered files exist (no base file)."""
    # Create only numbered files, no base file
    (tmp_path / "test-2.png").touch()
    (tmp_path / "test-3.png").touch()
    (tmp_path / "test-10.png").touch()

    result = _path_tools._next_filename(tmp_path, "test", "png")  # noqa: SLF001
    assert result == "test-11.png"  # Should be max + 1


# Fixtures for determine_path tests - testing various title scenarios
@pytest.fixture(
    params=[
        (
            {
                "layout": {
                    "title": {"text": "My-Test!@#$%^&*()Chart_with[lots]of{symbols}"},
                },
            },
            "My_TestChart_withlotsofsymbols",
        ),  # Complex title
        (
            {"layout": {"title": {"text": "Simple Title"}}},
            "Simple_Title",
        ),  # Simple title
        ({"layout": {}}, "fig"),  # No title
    ],
)
def fig_fixture(request):
    """Parameterized fixture for fig with various title scenarios."""
    return request.param


def test_determine_path_no_path_input(fig_fixture):
    """Test determine_path with no path input uses current path."""
    fig_dict, expected_prefix = fig_fixture
    result = _path_tools.determine_path(None, fig_dict, "ext")

    # Should use current directory
    assert result.parent.resolve() == Path().cwd().resolve()
    assert result.parent.is_dir()

    assert result.name == f"{expected_prefix}.ext"


def test_determine_path_no_suffix_directory(tmp_path, fig_fixture):
    """Test determine_path with path to directory having no suffix."""
    fig_dict, expected_prefix = fig_fixture

    # Test directory no suffix
    test_dir = tmp_path
    result = _path_tools.determine_path(test_dir, fig_dict, "ext")

    # Should use provided directory
    assert result.parent == test_dir
    assert result.name == f"{expected_prefix}.ext"

    # Test error
    nonexistent_dir = Path("/nonexistent/directory")
    with pytest.raises(ValueError, match="Directory .* not found. Please create it."):
        _path_tools.determine_path(nonexistent_dir, fig_dict, "ext")


def test_determine_path_directory_with_suffix(tmp_path, fig_fixture):
    """Test determine_path with path that is directory even with suffix."""
    fig_dict, expected_prefix = fig_fixture

    # Create a directory with a suffix-like name
    dir_with_suffix = tmp_path / "mydir.png"
    dir_with_suffix.mkdir()

    result = _path_tools.determine_path(dir_with_suffix, fig_dict, "ext")

    # Should treat as directory
    assert result.parent == dir_with_suffix
    assert result.name == f"{expected_prefix}.ext"


def test_determine_path_file_with_suffix(tmp_path, fig_fixture):
    """Test determine_path with file path having suffix."""
    fig_dict, expected_prefix = fig_fixture

    # Exists
    file_path = tmp_path / "output.png"
    result = _path_tools.determine_path(file_path, fig_dict, "ext")

    # Should return the exact path provided
    assert result == file_path

    # Doesn't exist
    file_path = Path("/nonexistent/directory/output.png")
    with pytest.raises(
        RuntimeError,
        match="Cannot reach path .* Are all directories created?",
    ):
        _path_tools.determine_path(file_path, fig_dict, "ext")

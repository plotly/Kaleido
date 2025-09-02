from pathlib import Path

import pytest

from kaleido._utils import get_path, is_httpish

pytestmark = pytest.mark.asyncio(loop_scope="function")

# ruff: noqa: S108


# Test get_path utility function
async def test_get_path_with_file_uri():
    """Test get_path function with file:// URIs."""
    file_uri = "file:///tmp/test.js"
    result = get_path(file_uri)
    assert result == Path("/tmp/test.js")


async def test_get_path_with_regular_path():
    """Test get_path function with regular file paths."""
    regular_path = "/tmp/test.js"
    result = get_path(regular_path)
    assert result == Path("/tmp/test.js")


async def test_get_path_with_http_url():
    """Test get_path function with HTTP URLs."""
    http_url = "https://example.com/test.js"
    result = get_path(http_url)
    assert result == Path("https://example.com/test.js")


# Test is_httpish utility function
async def test_is_httpish_with_http():
    """Test is_httpish function with HTTP URLs."""
    assert is_httpish("http://example.com/test.js") is True
    assert is_httpish("https://example.com/test.js") is True


async def test_is_httpish_with_file_paths():
    """Test is_httpish function with file paths."""
    assert is_httpish("/tmp/test.js") is False
    assert is_httpish("test.js") is False
    assert is_httpish("file:///tmp/test.js") is False


async def test_is_httpish_with_other_schemes():
    """Test is_httpish function with other URL schemes."""
    assert is_httpish("ftp://example.com/test.js") is False
    assert is_httpish("mailto:test@example.com") is False

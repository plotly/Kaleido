"""Integrative tests for all public API functions in __init__.py using basic figures."""

import warnings
from unittest.mock import patch

import pytest

import kaleido

# allows to create a browser pool for tests
pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest.fixture
def simple_figure():
    """Create a simple plotly figure for testing."""
    # ruff: noqa: PLC0415
    import plotly.express as px

    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        fig = px.line(x=[1, 2, 3, 4], y=[1, 2, 3, 4])

    return fig


async def test_calc_fig_basic(simple_figure):
    """Test calc_fig with a basic figure."""
    result = await kaleido.calc_fig(simple_figure)
    assert isinstance(result, bytes)
    assert len(result) > 0


def test_calc_fig_sync_basic_server_running(simple_figure):
    """Test calc_fig_sync when sync server is running."""
    with patch("kaleido._global_server.is_running", return_value=True), patch(
        "kaleido._global_server.call_function",
        return_value=b"test_bytes",
    ) as mock_call:
        result = kaleido.calc_fig_sync(simple_figure)

        mock_call.assert_called_once_with("calc_fig", simple_figure)
        assert result == b"test_bytes"


def test_calc_fig_sync_basic_server_not_running(simple_figure):
    """Test calc_fig_sync when sync server is not running."""
    with patch("kaleido._global_server.is_running", return_value=False), patch(
        "kaleido._sync_server.oneshot_async_run",
        return_value=b"test_bytes",
    ) as mock_oneshot:
        result = kaleido.calc_fig_sync(simple_figure)

        mock_oneshot.assert_called_once_with(
            kaleido.calc_fig,
            args=(simple_figure,),
            kwargs={},
        )
        assert result == b"test_bytes"


async def test_write_fig_basic(simple_figure, tmp_path):
    """Test write_fig with a basic figure."""
    output_file = tmp_path / "test_output.png"

    await kaleido.write_fig(simple_figure, path=str(output_file))

    # Check that file was created (actual implementation would create the file)
    # For this test we're just ensuring the function runs without error


def test_write_fig_sync_basic_server_running(simple_figure):
    """Test write_fig_sync when sync server is running."""
    with patch("kaleido._global_server.is_running", return_value=True), patch(
        "kaleido._global_server.call_function",
    ) as mock_call:
        kaleido.write_fig_sync(simple_figure, path="test.png")

        mock_call.assert_called_once_with("write_fig", simple_figure, path="test.png")


def test_write_fig_sync_basic_server_not_running(simple_figure):
    """Test write_fig_sync when sync server is not running."""
    with patch("kaleido._global_server.is_running", return_value=False), patch(
        "kaleido._sync_server.oneshot_async_run",
    ) as mock_oneshot:
        kaleido.write_fig_sync(simple_figure, path="test.png")

        mock_oneshot.assert_called_once_with(
            kaleido.write_fig,
            args=(simple_figure,),
            kwargs={"path": "test.png"},
        )


async def test_write_fig_from_object_basic(simple_figure):
    """Test write_fig_from_object with a basic figure generator."""
    generator = [simple_figure]

    # This should run without error
    await kaleido.write_fig_from_object(generator)


def test_write_fig_from_object_sync_basic_server_running(simple_figure):
    """Test write_fig_from_object_sync when sync server is running."""
    generator = [simple_figure]

    with patch("kaleido._global_server.is_running", return_value=True), patch(
        "kaleido._global_server.call_function",
    ) as mock_call:
        kaleido.write_fig_from_object_sync(generator)

        mock_call.assert_called_once_with("write_fig_from_object", generator)


def test_write_fig_from_object_sync_basic_server_not_running(simple_figure):
    """Test write_fig_from_object_sync when sync server is not running."""
    generator = [simple_figure]

    with patch("kaleido._global_server.is_running", return_value=False), patch(
        "kaleido._sync_server.oneshot_async_run",
    ) as mock_oneshot:
        kaleido.write_fig_from_object_sync(generator)

        mock_oneshot.assert_called_once_with(
            kaleido.write_fig_from_object,
            args=(generator,),
            kwargs={},
        )


def test_start_stop_sync_server_integration():
    """Test start_sync_server and stop_sync_server together."""
    # Test that we can start and stop the server without errors
    kaleido.start_sync_server(silence_warnings=True)
    kaleido.stop_sync_server(silence_warnings=True)


def test_sync_server_with_calc_fig_sync_integration(simple_figure):
    """Integration test: start server, use calc_fig_sync, then stop server."""
    # Start server
    kaleido.start_sync_server(silence_warnings=True)

    try:
        # Use calc_fig_sync - this should use the running server
        result = kaleido.calc_fig_sync(simple_figure)
        assert isinstance(result, bytes)
        assert len(result) > 0

    finally:
        # Always stop the server
        kaleido.stop_sync_server(silence_warnings=True)


def test_sync_server_with_write_fig_sync_integration(simple_figure, tmp_path):
    """Integration test: start server, use write_fig_sync, then stop server."""
    output_file = tmp_path / "test_integration.png"

    # Start server
    kaleido.start_sync_server(silence_warnings=True)

    try:
        # Use write_fig_sync - this should use the running server
        kaleido.write_fig_sync(simple_figure, path=str(output_file))

    finally:
        # Always stop the server
        kaleido.stop_sync_server(silence_warnings=True)

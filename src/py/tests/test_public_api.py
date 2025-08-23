"""Integrative tests for all public API functions in __init__.py using basic figures."""

import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

import kaleido


@pytest.fixture
def simple_figure():
    """Create a simple plotly figure for testing."""
    # ruff: noqa: PLC0415
    import plotly.express as px

    with warnings.catch_warnings():
        fig = px.line(x=[1, 2, 3, 4], y=[1, 2, 3, 4])

    return fig


async def test_calc_fig_basic(simple_figure):
    """Test calc_fig with a basic figure."""
    result = await kaleido.calc_fig(simple_figure)
    assert isinstance(result, bytes)
    assert result.startswith(b"\x89PNG\r\n\x1a\n"), "Not a PNG file"


async def test_calc_fig_sync_both_scenarios(simple_figure):
    """Test calc_fig_sync in both server running and not running scenarios."""
    # First get the expected result from calc_fig for comparison
    expected_result = await kaleido.calc_fig(simple_figure)
    assert isinstance(expected_result, bytes)
    assert expected_result.startswith(b"\x89PNG\r\n\x1a\n"), "Not a PNG file"

    # Test scenario 1: server running
    kaleido.start_sync_server(silence_warnings=True)
    try:
        with patch(
            "kaleido._global_server.call_function",
            wraps=kaleido._global_server.call_function,  # noqa: SLF001 internal
        ) as mock_call:
            result_server_running = kaleido.calc_fig_sync(simple_figure)

            mock_call.assert_called_once()
            assert isinstance(result_server_running, bytes)
            assert result_server_running.startswith(
                b"\x89PNG\r\n\x1a\n",
            ), "Not a PNG file"
            assert result_server_running == expected_result
    finally:
        kaleido.stop_sync_server(silence_warnings=True)

    # Test scenario 2: server not running
    with patch(
        "kaleido._sync_server.oneshot_async_run",
        wraps=kaleido._sync_server.oneshot_async_run,  # noqa: SLF001 internal
    ) as mock_oneshot:
        result_server_not_running = kaleido.calc_fig_sync(simple_figure)

        mock_oneshot.assert_called_once()
        assert isinstance(result_server_not_running, bytes)
        assert result_server_not_running.startswith(
            b"\x89PNG\r\n\x1a\n",
        ), "Not a PNG file"
        assert result_server_not_running == expected_result


async def test_write_fig_basic(simple_figure, tmp_path):
    """Test write_fig with a basic figure and compare with calc_fig output."""
    output_file = tmp_path / "test_output.png"

    # Get expected bytes from calc_fig
    expected_bytes = await kaleido.calc_fig(simple_figure)

    # Write figure to file
    await kaleido.write_fig(simple_figure, path=str(output_file))

    # Read the written file and compare
    with Path(output_file).open("rb") as f:  # noqa: ASYNC230 use aiofile
        written_bytes = f.read()

    assert written_bytes == expected_bytes
    assert written_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Not a PNG file"


async def test_write_fig_sync_both_scenarios(simple_figure, tmp_path):
    """Test write_fig_sync and write_fig_from_object_sync in both server scenarios."""
    # Get expected bytes from calc_fig for comparison
    expected_bytes = await kaleido.calc_fig(simple_figure)
    assert expected_bytes.startswith(b"\x89PNG\r\n\x1a\n"), "Not a PNG file"

    # Test scenario 1: server running
    output_file_1 = tmp_path / "test_server_running.png"
    output_file_from_object_1 = tmp_path / "test_from_object_server_running.png"
    kaleido.start_sync_server(silence_warnings=True)
    try:
        with patch(
            "kaleido._global_server.call_function",
            wraps=kaleido._global_server.call_function,  # noqa: SLF001 internal
        ) as mock_call:
            # Test write_fig_sync
            kaleido.write_fig_sync(simple_figure, path=str(output_file_1))

            # Test write_fig_from_object_sync
            kaleido.write_fig_from_object_sync(
                [
                    {
                        "fig": simple_figure,
                        "path": output_file_from_object_1,
                    },
                ],
            )

            # Should have been called twice (once for each function)
            assert mock_call.call_count == 2  # noqa: PLR2004

            # Read and verify the written files
            with Path(output_file_1).open("rb") as f:  # noqa: ASYNC230
                written_bytes_1 = f.read()
            assert written_bytes_1 == expected_bytes

            # Read and verify the written files
            with Path(output_file_from_object_1).open("rb") as f:  # noqa: ASYNC230
                from_object_written_bytes_1 = f.read()
            assert from_object_written_bytes_1 == expected_bytes

    finally:
        kaleido.stop_sync_server(silence_warnings=True)

    # Test scenario 2: server not running
    output_file_2 = tmp_path / "test_server_not_running.png"
    output_file_from_object_2 = tmp_path / "test_from_object_server_not_running.png"
    with patch(
        "kaleido._sync_server.oneshot_async_run",
        wraps=kaleido._sync_server.oneshot_async_run,  # noqa: SLF001 internal
    ) as mock_oneshot:
        # Test write_fig_sync
        kaleido.write_fig_sync(simple_figure, path=str(output_file_2))

        # Test write_fig_from_object_sync
        kaleido.write_fig_from_object_sync(
            [
                {
                    "fig": simple_figure,
                    "path": output_file_from_object_1,
                },
            ],
        )

        # Should have been called twice (once for each function)
        assert mock_oneshot.call_count == 2  # noqa: PLR2004

        # Read and verify the written files
        with Path(output_file_2).open("rb") as f:  # noqa: ASYNC230
            written_bytes_2 = f.read()
        assert written_bytes_2 == expected_bytes

        # Read and verify the written files
        with Path(output_file_from_object_2).open("rb") as f:  # noqa: ASYNC230
            from_object_written_bytes_2 = f.read()
        assert from_object_written_bytes_2 == expected_bytes


def test_start_stop_sync_server_integration():
    """Test start_sync_server and stop_sync_server with warning behavior."""
    # Test starting and stopping with warnings silenced
    kaleido.start_sync_server(silence_warnings=False)

    # Test starting already started server - should warn
    with pytest.warns(UserWarning, match="already"):
        kaleido.start_sync_server(silence_warnings=False)

    kaleido.start_sync_server(silence_warnings=True)

    kaleido.stop_sync_server(silence_warnings=False)

    # Test stopping already stopped server - should warn
    with pytest.warns(UserWarning, match="not running"):
        kaleido.stop_sync_server(silence_warnings=False)

    kaleido.stop_sync_server(silence_warnings=True)

"""Tests for wrapper functions in __init__.py that test argument passing."""

from unittest.mock import AsyncMock, patch

import kaleido

# Pretty complicated for basically testing a bunch of wrappers, but it works.
# Integration tests seem more important.


@patch("kaleido._sync_server.GlobalKaleidoServer.open")
def test_start_sync_server_passes_args(mock_open):
    """Test that start_sync_server passes args and silence_warnings correctly."""
    # Test with silence_warnings=False (default)
    args = ("arg1", "arg2")
    kwargs = {"key1": "value1", "key2": "value2"}

    kaleido.start_sync_server(*args, **kwargs)
    mock_open.assert_called_with(*args, silence_warnings=False, **kwargs)

    # Reset mock and test with silence_warnings=True
    mock_open.reset_mock()
    args = ("arg1",)
    kwargs = {"key1": "value1"}

    kaleido.start_sync_server(*args, silence_warnings=True, **kwargs)
    mock_open.assert_called_with(*args, silence_warnings=True, **kwargs)


@patch("kaleido._sync_server.GlobalKaleidoServer.close")
def test_stop_sync_server_passes_args(mock_close):
    """Test that stop_sync_server passes silence_warnings correctly."""
    # Test with silence_warnings=False (default)
    kaleido.stop_sync_server()
    mock_close.assert_called_with(silence_warnings=False)

    # Reset mock and test with silence_warnings=True
    mock_close.reset_mock()
    kaleido.stop_sync_server(silence_warnings=True)
    mock_close.assert_called_with(silence_warnings=True)


@patch("kaleido.Kaleido")
async def test_async_wrapper_functions(mock_kaleido_class):
    """Test all async wrapper functions pass arguments correctly."""
    # Create a mock that doesn't need the context fixture
    mock_kaleido_class.return_value = mock_kaleido = AsyncMock()
    mock_kaleido.__aenter__.return_value = mock_kaleido
    mock_kaleido.__aexit__.return_value = None
    mock_kaleido.calc_fig.return_value = b"test_bytes"

    fig = {"data": []}

    # Test calc_fig with full arguments and kopts forcing n=1
    path = "test.png"
    opts = {"width": 800}
    topojson = "test_topojson"
    kopts = {"some_option": "value"}

    result = await kaleido.calc_fig(fig, path, opts, topojson=topojson, kopts=kopts)

    expected_kopts = {"some_option": "value", "n": 1}
    mock_kaleido_class.assert_called_with(**expected_kopts)
    mock_kaleido.calc_fig.assert_called_with(
        fig,
        path=path,
        opts=opts,
        topojson=topojson,
    )
    assert result == b"test_bytes"

    # Reset mocks
    mock_kaleido_class.reset_mock()
    mock_kaleido.calc_fig.reset_mock()

    # Test calc_fig with empty kopts
    await kaleido.calc_fig(fig)
    mock_kaleido_class.assert_called_with(n=1)

    # Reset mocks
    mock_kaleido_class.reset_mock()
    mock_kaleido.write_fig.reset_mock()

    # Test write_fig with full arguments
    await kaleido.write_fig(fig, path, opts, topojson=topojson, kopts=kopts)
    mock_kaleido_class.assert_called_with(**kopts)  # write_fig doesn't force n=1
    mock_kaleido.write_fig.assert_called_with(
        fig,
        path=path,
        opts=opts,
        topojson=topojson,
    )

    # Reset mocks
    mock_kaleido_class.reset_mock()
    mock_kaleido.write_fig.reset_mock()

    # Test write_fig with empty kopts
    await kaleido.write_fig(fig)
    mock_kaleido_class.assert_called_with()

    # Reset mocks
    mock_kaleido_class.reset_mock()
    mock_kaleido.write_fig_from_object.reset_mock()

    # Test write_fig_from_object
    generator = [{"data": []}]
    await kaleido.write_fig_from_object(generator, kopts=kopts)
    mock_kaleido_class.assert_called_with(**kopts)
    mock_kaleido.write_fig_from_object.assert_called_with(generator)

"""Tests for wrapper functions in __init__.py that test argument passing."""

from unittest.mock import MagicMock, patch

import pytest

import kaleido


@pytest.fixture
def mock_kaleido_context():
    """Fixture that provides a mocked Kaleido context manager."""
    mock_kaleido = MagicMock()
    mock_kaleido.__aenter__ = MagicMock(return_value=mock_kaleido)
    mock_kaleido.__aexit__ = MagicMock(return_value=False)
    return mock_kaleido


@patch("kaleido._sync_server.GlobalKaleidoServer.open")
def test_start_sync_server_passes_args(mock_open):
    """Test that start_sync_server passes args to GlobalKaleidoServer.open."""
    args = ("arg1", "arg2")
    kwargs = {"key1": "value1", "key2": "value2"}

    kaleido.start_sync_server(*args, **kwargs)

    mock_open.assert_called_once_with(*args, silence_warnings=False, **kwargs)


@patch("kaleido._sync_server.GlobalKaleidoServer.open")
def test_start_sync_server_silence_warnings(mock_open):
    """Test that start_sync_server passes silence_warnings parameter correctly."""
    args = ("arg1",)
    kwargs = {"key1": "value1"}

    kaleido.start_sync_server(*args, silence_warnings=True, **kwargs)

    mock_open.assert_called_once_with(*args, silence_warnings=True, **kwargs)


@patch("kaleido._sync_server.GlobalKaleidoServer.close")
def test_stop_sync_server_passes_args(mock_close):
    """Test that stop_sync_server passes silence_warnings to GlobalKaleidoServer."""
    kaleido.stop_sync_server()

    mock_close.assert_called_once_with(silence_warnings=False)


@patch("kaleido._sync_server.GlobalKaleidoServer.close")
def test_stop_sync_server_silence_warnings(mock_close):
    """Test that stop_sync_server passes silence_warnings=True correctly."""
    kaleido.stop_sync_server(silence_warnings=True)

    mock_close.assert_called_once_with(silence_warnings=True)


@patch("kaleido.Kaleido")
@pytest.mark.asyncio
async def test_calc_fig_passes_args_and_forces_n_to_1(
    mock_kaleido_class,
    mock_kaleido_context,
):
    """Test that calc_fig passes args correctly and forces n=1 in kopts."""
    mock_kaleido_context.calc_fig.return_value = b"test_bytes"
    mock_kaleido_class.return_value = mock_kaleido_context

    fig = {"data": []}
    path = "test.png"
    opts = {"width": 800}
    topojson = "test_topojson"
    kopts = {"some_option": "value"}

    result = await kaleido.calc_fig(fig, path, opts, topojson=topojson, kopts=kopts)

    # Check that Kaleido was instantiated with kopts including n=1
    expected_kopts = {"some_option": "value", "n": 1}
    mock_kaleido_class.assert_called_once_with(**expected_kopts)

    # Check that calc_fig was called with correct arguments
    mock_kaleido_context.calc_fig.assert_called_once_with(
        fig,
        path=path,
        opts=opts,
        topojson=topojson,
    )

    assert result == b"test_bytes"


@patch("kaleido.Kaleido")
@pytest.mark.asyncio
async def test_calc_fig_empty_kopts(mock_kaleido_class, mock_kaleido_context):
    """Test that calc_fig works with empty kopts."""
    mock_kaleido_context.calc_fig.return_value = b"test_bytes"
    mock_kaleido_class.return_value = mock_kaleido_context

    fig = {"data": []}

    await kaleido.calc_fig(fig)

    # Check that Kaleido was instantiated with only n=1
    mock_kaleido_class.assert_called_once_with(n=1)


@patch("kaleido.Kaleido")
@pytest.mark.asyncio
async def test_write_fig_passes_args(mock_kaleido_class, mock_kaleido_context):
    """Test that write_fig passes all arguments correctly."""
    mock_kaleido_class.return_value = mock_kaleido_context

    fig = {"data": []}
    path = "test.png"
    opts = {"width": 800}
    topojson = "test_topojson"
    kopts = {"some_option": "value"}

    await kaleido.write_fig(fig, path, opts, topojson=topojson, kopts=kopts)

    # Check that Kaleido was instantiated with kopts
    mock_kaleido_class.assert_called_once_with(**kopts)

    # Check that write_fig was called with correct arguments
    mock_kaleido_context.write_fig.assert_called_once_with(
        fig,
        path=path,
        opts=opts,
        topojson=topojson,
    )


@patch("kaleido.Kaleido")
@pytest.mark.asyncio
async def test_write_fig_empty_kopts(mock_kaleido_class, mock_kaleido_context):
    """Test that write_fig works with empty kopts."""
    mock_kaleido_class.return_value = mock_kaleido_context

    fig = {"data": []}

    await kaleido.write_fig(fig)

    # Check that Kaleido was instantiated with empty dict
    mock_kaleido_class.assert_called_once_with()


@patch("kaleido.Kaleido")
@pytest.mark.asyncio
async def test_write_fig_from_object_passes_args(
    mock_kaleido_class,
    mock_kaleido_context,
):
    """Test that write_fig_from_object passes all arguments correctly."""
    mock_kaleido_class.return_value = mock_kaleido_context

    generator = [{"data": []}]
    kopts = {"some_option": "value"}

    await kaleido.write_fig_from_object(generator, kopts=kopts)

    # Check that Kaleido was instantiated with kopts
    mock_kaleido_class.assert_called_once_with(**kopts)

    # Check that write_fig_from_object was called with correct arguments
    mock_kaleido_context.write_fig_from_object.assert_called_once_with(generator)

from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from kaleido import Kaleido


@pytest.fixture
async def simple_figure_with_bytes(tmp_path):
    """Create a simple figure with calculated bytes and PNG assertion."""
    import plotly.express as px  # noqa: PLC0415

    fig = px.line(x=[1, 2, 3], y=[1, 2, 3])
    path = tmp_path / "test_figure.png"

    async with Kaleido() as k:
        bytes_data = await k.calc_fig(
            fig,
            opts={"format": "png", "width": 400, "height": 300},
        )

    # Assert it's a PNG by checking the PNG signature
    assert bytes_data[:8] == b"\x89PNG\r\n\x1a\n", "Generated data is not a valid PNG"

    return {
        "fig": fig,
        "bytes": bytes_data,
        "path": path,
        "opts": {"format": "png", "width": 400, "height": 300},
    }


async def test_write_fig_from_object_sync_generator(simple_figure_with_bytes, tmp_path):
    """Test write_fig_from_object with sync generator."""

    file_paths = []

    def fig_generator():
        for i in range(2):
            path = tmp_path / f"test_sync_{i}.png"
            file_paths.append(path)
            yield {
                "fig": simple_figure_with_bytes["fig"],
                "path": path,
                "opts": simple_figure_with_bytes["opts"],
            }

    async with Kaleido() as k:
        await k.write_fig_from_object(fig_generator())

    # Assert that each created file matches the fixture bytes
    for path in file_paths:
        assert path.exists(), f"File {path} was not created"
        created_bytes = path.read_bytes()
        assert created_bytes == simple_figure_with_bytes["bytes"], (
            f"File {path} bytes don't match fixture bytes"
        )


async def test_write_fig_from_object_async_generator(
    simple_figure_with_bytes,
    tmp_path,
):
    """Test write_fig_from_object with async generator."""

    file_paths = []

    async def fig_async_generator():
        for i in range(2):
            path = tmp_path / f"test_async_{i}.png"
            file_paths.append(path)
            yield {
                "fig": simple_figure_with_bytes["fig"],
                "path": path,
                "opts": simple_figure_with_bytes["opts"],
            }

    async with Kaleido() as k:
        await k.write_fig_from_object(fig_async_generator())

    # Assert that each created file matches the fixture bytes
    for path in file_paths:
        assert path.exists(), f"File {path} was not created"
        created_bytes = path.read_bytes()
        assert created_bytes == simple_figure_with_bytes["bytes"], (
            f"File {path} bytes don't match fixture bytes"
        )


async def test_write_fig_from_object_iterator(simple_figure_with_bytes, tmp_path):
    """Test write_fig_from_object with iterator."""

    fig_list = []
    file_paths = []
    for i in range(2):
        path = tmp_path / f"test_iter_{i}.png"
        file_paths.append(path)
        fig_list.append(
            {
                "fig": simple_figure_with_bytes["fig"],
                "path": path,
                "opts": simple_figure_with_bytes["opts"],
            },
        )

    async with Kaleido() as k:
        await k.write_fig_from_object(fig_list)

    # Assert that each created file matches the fixture bytes
    for path in file_paths:
        assert path.exists(), f"File {path} was not created"
        created_bytes = path.read_bytes()
        assert created_bytes == simple_figure_with_bytes["bytes"], (
            f"File {path} bytes don't match fixture bytes"
        )


async def test_write_fig_from_object_bare_dictionary(
    simple_figure_with_bytes,
    tmp_path,
):
    """Test write_fig_from_object with bare dictionary list."""

    path1 = tmp_path / "test_dict_1.png"
    path2 = tmp_path / "test_dict_2.png"

    fig_data = [
        {
            "fig": simple_figure_with_bytes["fig"],
            "path": path1,
            "opts": simple_figure_with_bytes["opts"],
        },
        {
            "fig": simple_figure_with_bytes["fig"].to_dict(),
            "path": path2,
            "opts": simple_figure_with_bytes["opts"],
        },
    ]

    async with Kaleido() as k:
        await k.write_fig_from_object(fig_data)

    # Assert that each created file matches the fixture bytes
    for path in [path1, path2]:
        assert path.exists(), f"File {path} was not created"
        created_bytes = path.read_bytes()
        assert created_bytes == simple_figure_with_bytes["bytes"], (
            f"File {path} bytes don't match fixture bytes"
        )


@given(
    path=st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=["L", "N"]),
    ),
    width=st.integers(min_value=100, max_value=2000),
    height=st.integers(min_value=100, max_value=2000),
    format_type=st.sampled_from(["png", "svg", "pdf", "html"]),
    topojson=st.one_of(st.none(), st.text(min_size=1, max_size=20)),
)
async def test_write_fig_argument_passthrough(  #  noqa: PLR0913
    simple_figure_with_bytes,
    tmp_path,
    path,
    width,
    height,
    format_type,
    topojson,
):
    """Test that write_fig properly passes arguments to write_fig_from_object."""

    test_path = tmp_path / f"{path}.{format_type}"
    opts = {"format": format_type, "width": width, "height": height}

    # Mock write_fig_from_object to capture arguments
    with patch.object(Kaleido, "write_fig_from_object") as mock_write_fig_from_object:
        async with Kaleido() as k:
            await k.write_fig(
                simple_figure_with_bytes["fig"],
                path=test_path,
                opts=opts,
                topojson=topojson,
            )

        # Verify write_fig_from_object was called
        mock_write_fig_from_object.assert_called_once()

        # Extract the generator that was passed as first argument
        args, kwargs = mock_write_fig_from_object.call_args
        assert len(args) == 1, "Expected exactly one argument (the generator)"

        generator = args[0]

        # Convert generator to list to inspect its contents
        generated_args_list = list(generator)
        assert len(generated_args_list) == 1, (
            "Expected generator to yield exactly one item"
        )

        generated_args = generated_args_list[0]

        # Validate that the generated arguments match what we passed to write_fig
        assert "fig" in generated_args, "Generated args should contain 'fig'"
        assert "path" in generated_args, "Generated args should contain 'path'"
        assert "opts" in generated_args, "Generated args should contain 'opts'"
        assert "topojson" in generated_args, "Generated args should contain 'topojson'"

        # Check that the values match
        assert generated_args["fig"] == simple_figure_with_bytes["fig"], (
            "Figure should match"
        )  # this should fail
        assert str(generated_args["path"]) == str(test_path), "Path should match"
        assert generated_args["opts"] == opts, "Options should match"
        assert generated_args["topojson"] == topojson, "Topojson should match"

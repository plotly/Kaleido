from __future__ import annotations

import argparse
import sys
from pathlib import Path

import logistro

from . import _defaults

_logger = logistro.getLogger(__name__)

description = """kaleido_mocker will load up json files of plotly figs and export them.

If you set multiple process, -n, non-headless mode won't function well because
chrome will actually throttle tabs or windows/visibile- unless that tab/window
is headless.

The export of the program is a json object containing information about the execution.
"""

if "--headless" in sys.argv and "--no-headless" in sys.argv:
    raise ValueError(
        "Choose either '--headless' or '--no-headless'.",
    )

parser = argparse.ArgumentParser(
    add_help=True,
    parents=[logistro.parser],
    conflict_handler="resolve",
    description=description,
)

# Overrides logstro default
parser.add_argument(
    "--logistro-level",
    default="INFO",
    dest="log",
    help="Set the logging level (default INFO)",
)

basic_config = parser.add_argument_group("Basic Config Options")

basic_config.add_argument(
    "--n",
    type=int,
    default=_defaults.cpus,
    help="Number of tabs, defaults to # of cpus",
)
basic_config.add_argument(
    "--input",
    type=str,
    default=_defaults.in_dir,
    help="Directory of mock file/s or single file (default tests/mocks)",
)
basic_config.add_argument(
    "--output",
    type=str,
    default=_defaults.out_dir,
    help="DIRECTORY of mock file/s (default tests/renders)",
)

basic_config.add_argument(
    "--timeout",
    type=int,
    default=90,
    help="Set timeout in seconds for any 1 mock (default 60 seconds)",
)

basic_config.add_argument(
    "--fail-fast",
    action="store_true",
    default=False,
    help="Throw first error encountered and stop execution.",
)

basic_config.add_argument(
    "--random",
    type=int,
    default=0,
    help="Will select N random jsons- or if 0 (default), all.",
)

# Image Setting Arguments

image_parameters = parser.add_argument_group("Image Parameterize")

image_parameters.add_argument(
    "--parameterize",
    action="store_true",
    default=False,
    help="Run mocks w/ different configurations.",
)

image_parameters.add_argument(
    "--format",
    type=str,
    default=argparse.SUPPRESS,
    help="png (default), pdf, jpg, webp, svg, json",
)
image_parameters.add_argument(
    "--width",
    type=str,
    default=argparse.SUPPRESS,
    help="width in pixels (default 700)",
)
image_parameters.add_argument(
    "--height",
    type=str,
    default=argparse.SUPPRESS,
    help="height in pixels (default 500)",
)
image_parameters.add_argument(
    "--scale",
    type=str,
    default=argparse.SUPPRESS,
    help="Scale ratio, acts as multiplier for height/width (default 1)",
)

# Diagnostic Arguments

diagnostic_options = parser.add_argument_group("Diagnostic Options")

diagnostic_options.add_argument(
    "--headless",
    action="store_true",
    default=True,
    help="Set headless as True (default)",
)
diagnostic_options.add_argument(
    "--no-headless",
    action="store_false",
    dest="headless",
    help="Set headless as False",
)

diagnostic_options.add_argument(
    "--stepper",
    action="store_true",
    default=False,
    dest="stepper",
    help="Stepper sets n to 1, headless to False, no timeout "
    "and asks for confirmation before printing.",
)


args = parser.parse_args()

logistro.getLogger().setLevel(args.log)

if not Path(args.output).is_dir():
    raise ValueError(f"Specified output must be existing directory. Is {args.output!s}")

args_d = vars(args)
if args_d["stepper"]:
    args_d["n"] = 1
    args_d["headless"] = True
    args_d["timeout"] = 0

_p = args_d["parameterize"]

args_d.setdefault("width", _defaults.width if _p else _defaults.width[0])
args_d.setdefault("height", _defaults.height if _p else _defaults.height[0])
args_d.setdefault("scale", _defaults.scale if _p else _defaults.scale[0])
args_d.setdefault("format", _defaults.extension if _p else _defaults.extension[0])

for key in ("width", "height", "scale", "format"):
    if not isinstance(args_d[key], (list, tuple)):
        args_d[key] = args_d[key]

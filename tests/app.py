import asyncio
import argparse
from pathlib import Path

import baile

# Extract jsons of mocks
dir_in = Path(__file__).resolve().parent / "mocks"
results_dir = Path(__file__).resolve().parent / "images"

parser = argparse.ArgumentParser()
parser.add_argument("--n_tabs", type=int, default=4, help="Number of tabs")
parser.add_argument("--path_mock", type=str, default=dir_in, help="Directory of mock file/s")
args = parser.parse_args()
arg_dict = vars(args)


# Loop to generate images of the jsons
async def process_images():
    try:
        # Process to generete images of the json
        await baile.to_image(
            path_figs=arg_dict["path_mock"],
            path=str(results_dir),
            num_tabs=arg_dict["n_tabs"],
            debug=True,
            headless=False,
        )
    except Exception as e:
        print("No to image".center(30, "%"))
        print(e)
        print("***")


# Run the loop
asyncio.run(process_images())

import os
import json
import asyncio
from pathlib import Path

import baile

# Extract jsons of mocks
dir_in = Path(__file__).resolve().parent / "mocks/"
ALL_MOCKS = [os.path.splitext(a)[0] for a in os.listdir(dir_in) if a.endswith(".json")]
ALL_MOCKS.sort()
all_names = ALL_MOCKS


# Loop to generate images of the jsons
async def process_images():
    for name in all_names:
        # read json
        json_path = os.path.join(dir_in, name + ".json")
        try:
            # Process to generete images of the json
            await baile.to_image(json_path)
        except Exception as e:
            print("No to image")
            print(e)
            print(json_path)
            print("***")


# Run the loop
asyncio.run(process_images())

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
        with open(os.path.join(dir_in, name + ".json"), "r") as _in:
            try:
                # Load json as obj
                fig = json.load(_in)
            except Exception as e:
                print("No load")
                print(e)
                print(_in)
                print("***")
                continue

            # Set diomensions
            width = 700
            height = 500
            if "layout" in fig:
                layout = fig["layout"]
                if "autosize" not in layout or layout["autosize"] != True:
                    if "width" in layout:
                        width = layout["width"]
                    if "height" in layout:
                        height = layout["height"]
            try:
                # Process to generete images of the json
                img_data = await baile.to_image(
                    fig, format="png", width=width, height=height
                )

                # Set path of tyhe image file
                output_file = f"./results/{name}.png"

                # Write image file
                with open(output_file, "wb") as out_file:
                    out_file.write(img_data)
                print(f"Image saved to {output_file}")
            except Exception as e:
                print("No to image")
                print(e)
                print(_in)
                print("***")


# Run the loop
asyncio.run(process_images())

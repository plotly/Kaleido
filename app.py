import os
import json

from pathlib import Path
from .baile.process_images import transform

dirIn = Path(__file__).resolve().parent / "mocks/"
ALL_MOCKS = [os.path.splitext(a)[0] for a in os.listdir(dirIn) if a.endswith(".json")]
ALL_MOCKS.sort()
allNames = ALL_MOCKS


for name in allNames:
    with open(os.path.join(dirIn, name + ".json"), "r") as _in:
        try:
            fig = json.load(_in)
        except Exception as e:
            print("No load")
            print(e)
            print(_in)
            print("***")
            continue

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
            img_data = transform(fig, format="png", width=width, height=height)
            output_file = f"./results/{name}.png"
            with open(output_file, "wb") as out_file:
                out_file.write(img_data)
            print(f"Image saved to {output_file}")
        except Exception as e:
            print("No to image")
            print(e)
            print(_in)
            print("***")

from pathlib import Path
import warnings

import choreographer as choreo

from .tab import Tab

# Path of the page to use
SCRIPT_PATH = Path(__file__).resolve().parent / "vendor" / "index.html"


class Browser(choreo.browser.Browser):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def create_tab(self, url=SCRIPT_PATH.as_uri(), width=None, height=None):
        if not self.loop:
            raise RuntimeError(
                "There is no eventloop, or was not passed to browser. Cannot use async methods"
            )
        if self.headless and (width or height):
            warnings.warn(
                "Width and height only work for headless chrome mode, they will be ignored."
            )
            width = None
            height = None
        params = dict(url=url)
        if width:
            params["width"] = width
        if height:
            params["height"] = height

        response = await self.browser.send_command("Target.createTarget", params=params)
        if "error" in response:
            raise RuntimeError(
                "Could not create tab"
            ) from choreo.DevtoolsProtocolError(response)
        target_id = response["result"]["targetId"]
        new_tab = Tab(target_id, self)
        self._add_tab(new_tab)
        await new_tab.create_session()
        return new_tab

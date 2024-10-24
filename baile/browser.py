import warnings

import choreographer as choreo

from .tab import Tab
from .prepare import SCRIPT_PATH


class Browser(choreo.browser.Browser):
    def __init__(
        self,
        path=None,
        headless=True,
        loop=None,
        executor=None,
        debug=False,
        debug_browser=None,
    ):
        super().__init__(
            path,
            headless,
            loop,
            executor,
            debug,
            debug_browser,
        )

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

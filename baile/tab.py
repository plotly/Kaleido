import choreographer as choreo
from .prepare import SCRIPT_PATH


class Tab(choreo.tab.Tab):
    async def __init__(self, browser):
        tab, browser = await self.create(browser)
        super().__init__(tab.target_id, browser)
    
    async def create(self, browser):
        tab = await browser.create_tab(SCRIPT_PATH.as_uri())
        return tab, browser

    async def reload(self):
        return await self.send_command(
            "Page.reload"
        )  # The return is not necessary but just in case

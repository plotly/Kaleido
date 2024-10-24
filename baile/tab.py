import choreographer as choreo
from .prepare import SCRIPT_PATH


class Tab(choreo.tab.Tab):
    def __init__(self, target_id, browser):
        super().__init__(target_id, browser)

    @classmethod
    async def create(cls, browser):
        tab = await browser.create_tab(SCRIPT_PATH.as_uri())
        return cls(tab.target_id, browser)

    async def reload(self):
        return await self.send_command(
            "Page.reload"
        )  # The return is not necessary but just in case

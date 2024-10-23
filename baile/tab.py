import choreographer as choreo


class Tab(choreo.Tab):
    def __init__(self, target_id, browser):
        super().__init__(target_id, browser)

    async def reload(self):
        return await self.send_command(
            "Page.reload"
        )  # The return is not necessary but just in case

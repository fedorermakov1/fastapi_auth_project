class FakeTaskRepository:
    async def get_all_by_user(self, user_id):
        return []


class FakeUnitOfWork:
    def __init__(self):
        self.tasks = FakeTaskRepository()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass
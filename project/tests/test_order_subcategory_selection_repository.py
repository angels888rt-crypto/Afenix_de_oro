import asyncio

from app.infrastructure.database.repositories.base_repositories import (
    OrderItemSubcategorySelectionRepository,
)


class FakeSession:
    def __init__(self):
        self.added = []
        self.committed = False

    def add(self, selection):
        self.added.append(selection)

    async def commit(self):
        self.committed = True

    async def refresh(self, _selection):
        pass


def test_create_order_item_selection_uses_existing_model_columns() -> None:
    session = FakeSession()
    repository = OrderItemSubcategorySelectionRepository(session)

    selection = asyncio.run(repository.create(12, 4, 9))

    assert selection.order_item_id == 12
    assert selection.subcategory_id == 4
    assert selection.option_id == 9
    assert session.added == [selection]
    assert session.committed is True

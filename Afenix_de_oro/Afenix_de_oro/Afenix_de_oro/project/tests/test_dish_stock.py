import pytest

from app.application.use_cases.dish_use_cases import UpdateDishUseCase
from app.domain.entities import Dish


class FakeDishRepository:
    def __init__(self, dish: Dish):
        self._dish = dish
        self.updated_dish = None

    async def get_by_id(self, dish_id: int):
        return self._dish

    async def update(self, dish_id: int, dish: Dish):
        self.updated_dish = (dish_id, dish)
        return dish


@pytest.mark.asyncio
async def test_update_use_case_persists_availability():
    dish = Dish(
        id=1,
        name="Arroz",
        price=1200,
        estimated_time=20,
        category="principal",
        is_available=True,
    )
    repository = FakeDishRepository(dish)
    use_case = UpdateDishUseCase(repository)

    updated = await use_case.execute(dish_id=1, is_available=False, updated_by=7)

    assert updated.is_available is False
    assert repository.updated_dish[0] == 1
    assert repository.updated_dish[1].is_available is False

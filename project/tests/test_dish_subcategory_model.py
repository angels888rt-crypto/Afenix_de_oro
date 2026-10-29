from app.infrastructure.database.models import DishSubcategoryModel


def test_dish_subcategory_model_matches_composite_primary_key_schema() -> None:
    table = DishSubcategoryModel.__table__

    assert set(table.primary_key.columns.keys()) == {"dish_id", "subcategory_id"}
    assert set(table.columns.keys()) == {"dish_id", "subcategory_id"}

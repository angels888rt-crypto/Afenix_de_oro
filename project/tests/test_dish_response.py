from datetime import datetime, timezone

from app.application.dto import DishResponse


def test_dish_response_allows_missing_preparation_notes() -> None:
    response = DishResponse(
        id=1,
        name="Arroz",
        description="Arroz con pollo",
        price=1200,
        estimated_time=600,
        category="PLATO FUERTE",
        is_available=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    assert response.preparation_notes is None

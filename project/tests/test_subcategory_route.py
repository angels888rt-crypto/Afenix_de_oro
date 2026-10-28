from main import app


def test_subcategory_collection_route_is_registered() -> None:
    route = next(
        route
        for route in app.routes
        if route.path == "/api/v1/subcategories" and "GET" in route.methods
    )

    assert route.name == "list_subcategories"

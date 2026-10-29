from sqlalchemy import create_engine, inspect, text

from app.infrastructure.database.session import _ensure_subcategory_schema


def test_ensure_subcategory_schema_adds_fields_missing_from_legacy_tables() -> None:
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE TABLE subcategories ("
                    "id INTEGER PRIMARY KEY, name VARCHAR(80) NOT NULL, "
                    "description VARCHAR(200), created_at DATETIME NOT NULL, "
                    "updated_at DATETIME NOT NULL, deleted_at DATETIME, "
                    "created_by INTEGER, updated_by INTEGER)"
                )
            )
            connection.execute(
                text(
                    "CREATE TABLE subcategory_options ("
                    "id INTEGER PRIMARY KEY, subcategory_id INTEGER NOT NULL, "
                    "name VARCHAR(80) NOT NULL, created_at DATETIME NOT NULL, "
                    "updated_at DATETIME NOT NULL, deleted_at DATETIME, "
                    "created_by INTEGER, updated_by INTEGER)"
                )
            )

            _ensure_subcategory_schema(connection)

            subcategory_columns = {
                column["name"]
                for column in inspect(connection).get_columns("subcategories")
            }
            option_columns = {
                column["name"]
                for column in inspect(connection).get_columns("subcategory_options")
            }

        assert "is_active" in subcategory_columns
        assert "sort_order" in option_columns
    finally:
        engine.dispose()

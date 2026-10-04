from sqlalchemy import inspect

from api.database.database import (
    engine,
    init_db,
)


def main():
    init_db()

    inspector = inspect(engine)

    print("Database initialized.")
    print("Tables:")

    for table in inspector.get_table_names():
        print(f"- {table}")


if __name__ == "__main__":
    main()
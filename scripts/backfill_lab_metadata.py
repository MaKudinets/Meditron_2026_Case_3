"""
Backfill missing laboratory metadata in existing LabValue rows.

Скрипт предназначен только для уже существующих записей истории.

Он НЕ:
- меняет схему базы данных;
- меняет результаты ML;
- меняет значения лабораторных показателей;
- меняет Screening.result_data;
- перезаписывает уже существующие unit/reference values.

По умолчанию работает в режиме DRY RUN.

Для реального применения нужно явно передать:

    --apply
"""

from pathlib import Path
import argparse
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# IMPORTS
# ============================================================

from sqlalchemy import select

from api.database.database import (
    SessionLocal,
)

from api.database.models import (
    LabValue,
)

from api.resources.lab_catalog import (
    get_lab_catalog_metadata,
)


# ============================================================
# HELPERS
# ============================================================


def unit_is_missing(
    unit,
) -> bool:
    if unit is None:
        return True

    if isinstance(
        unit,
        str,
    ):
        return not bool(
            unit.strip()
        )

    return False


def build_updates(
    lab_value: LabValue,
) -> dict:
    """
    Определяет, какие поля можно безопасно заполнить.

    Уже существующие значения никогда
    не перезаписываются.
    """

    catalog = (
        get_lab_catalog_metadata(
            lab_value.feature
        )
    )

    if not catalog:
        return {}

    updates = {}

    # ========================================================
    # UNIT
    # ========================================================

    catalog_unit = catalog.get(
        "unit"
    )

    if (
        unit_is_missing(
            lab_value.unit
        )
        and catalog_unit
    ):
        updates[
            "unit"
        ] = catalog_unit

    # ========================================================
    # REFERENCES
    # ========================================================

    has_existing_reference = (
        lab_value.reference_low
        is not None
        or lab_value.reference_high
        is not None
    )

    catalog_low = catalog.get(
        "reference_low"
    )

    catalog_high = catalog.get(
        "reference_high"
    )

    has_catalog_reference = (
        catalog_low is not None
        or catalog_high is not None
    )

    # Очень важное ограничение:
    #
    # если запись уже имеет reference_source,
    # например lab_file или manual,
    # мы не подменяем её внутренним диапазоном.
    #
    # Это защищает старые лабораторные данные
    # от незаметной замены.
    can_use_catalog_reference = (
        not has_existing_reference
        and has_catalog_reference
        and (
            lab_value.reference_source
            is None
            or lab_value.reference_source
            == "internal_catalog"
        )
    )

    if can_use_catalog_reference:

        updates[
            "reference_low"
        ] = catalog_low

        updates[
            "reference_high"
        ] = catalog_high

        updates[
            "reference_source"
        ] = "internal_catalog"

    return updates


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Fill missing LabValue metadata "
            "from the internal laboratory catalog."
        )
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help=(
            "Actually write changes to the database. "
            "Without this flag the script is dry-run only."
        ),
    )

    args = parser.parse_args()

    db = SessionLocal()

    scanned_rows = 0
    changed_rows = 0
    unit_updates = 0
    reference_updates = 0

    preview_limit = 20
    preview_count = 0

    try:
        lab_values = list(
            db.scalars(
                select(
                    LabValue
                )
            ).all()
        )

        for lab_value in lab_values:

            scanned_rows += 1

            updates = build_updates(
                lab_value
            )

            if not updates:
                continue

            changed_rows += 1

            if "unit" in updates:
                unit_updates += 1

            if (
                "reference_low" in updates
                or "reference_high" in updates
            ):
                reference_updates += 1

            if preview_count < preview_limit:

                print(
                    f"[{lab_value.id}] "
                    f"{lab_value.feature}: "
                    f"{updates}"
                )

                preview_count += 1

            if args.apply:

                for field, value in (
                    updates.items()
                ):
                    setattr(
                        lab_value,
                        field,
                        value,
                    )

        # ====================================================
        # COMMIT / DRY RUN
        # ====================================================

        if args.apply:
            db.commit()

        else:
            # Никакие изменения не должны
            # попасть в БД в dry-run.
            db.rollback()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print(
        "========================================"
    )

    if args.apply:
        print(
            "MODE: APPLY"
        )
    else:
        print(
            "MODE: DRY RUN"
        )

    print(
        "========================================"
    )

    print(
        f"Scanned LabValue rows: "
        f"{scanned_rows}"
    )

    print(
        f"Rows requiring changes: "
        f"{changed_rows}"
    )

    print(
        f"Unit updates: "
        f"{unit_updates}"
    )

    print(
        f"Reference updates: "
        f"{reference_updates}"
    )

    if not args.apply:

        print()
        print(
            "No database changes were committed."
        )

        print(
            "Run again with --apply "
            "only after reviewing this output."
        )


if __name__ == "__main__":
    main()

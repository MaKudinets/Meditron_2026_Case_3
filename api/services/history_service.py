from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import (
    LabValue,
    PatientProfile,
    Screening,
    User,
)

from api.resources.lab_catalog import (
    get_lab_catalog_metadata,
)


class PatientProfileNotFoundError(
    ValueError
):
    pass


class ScreeningNotFoundError(
    ValueError
):
    pass


class PatientRoleRequiredError(
    ValueError
):
    pass


# ============================================================
# LAB METADATA
# ============================================================


def _metadata_to_dict(
    metadata,
) -> dict:
    """
    Приводит metadata к обычному dict.

    В текущем API metadata уже приходит как dict,
    но эта проверка делает функцию безопаснее,
    если в будущем сюда попадёт Pydantic-модель.
    """

    if metadata is None:
        return {}

    if isinstance(
        metadata,
        dict,
    ):
        return metadata

    if hasattr(
        metadata,
        "model_dump",
    ):
        return metadata.model_dump(
            mode="json"
        )

    return {}


def _clean_unit(
    unit,
):
    """
    Пустую строку единицы измерения
    считаем отсутствующим значением.
    """

    if unit is None:
        return None

    if isinstance(
        unit,
        str,
    ):
        unit = unit.strip()

        if not unit:
            return None

    return unit


def resolve_lab_metadata(
    *,
    feature: str,
    metadata,
    reference_source: str | None,
) -> dict:
    """
    Определяет metadata, которые будут сохранены в LabValue.

    Приоритет:

    1. metadata конкретного анализа / файла;
    2. backend-каталог;
    3. None.

    Важно:
    - данные лаборатории не перезаписываются каталогом;
    - диагностические пороги ML/expert system здесь
      не используются;
    - функция никак не участвует в ML inference.
    """

    incoming = _metadata_to_dict(
        metadata
    )

    catalog = (
        get_lab_catalog_metadata(
            feature
        )
    )

    # ========================================================
    # UNIT
    # ========================================================

    incoming_unit = _clean_unit(
        incoming.get(
            "unit"
        )
    )

    catalog_unit = _clean_unit(
        catalog.get(
            "unit"
        )
    )

    unit = (
        incoming_unit
        if incoming_unit is not None
        else catalog_unit
    )

    # ========================================================
    # REFERENCE
    # ========================================================

    incoming_low = incoming.get(
        "reference_low"
    )

    incoming_high = incoming.get(
        "reference_high"
    )

    reference_text = incoming.get(
        "reference_text"
    )

    has_incoming_reference = (
        incoming_low is not None
        or incoming_high is not None
    )

    has_reference_text = (
        isinstance(
            reference_text,
            str,
        )
        and bool(
            reference_text.strip()
        )
    )

    # Если лаборатория передала распознанный
    # референс, используем только его.
    if has_incoming_reference:

        return {
            "unit": unit,

            "reference_low": (
                incoming_low
            ),

            "reference_high": (
                incoming_high
            ),

            "reference_source": (
                reference_source
            ),
        }

    # Если в лабораторном файле был текст
    # референса, но парсер не смог безопасно
    # превратить его в числа, не подменяем
    # лабораторный диапазон внутренним.
    if has_reference_text:

        return {
            "unit": unit,

            "reference_low": None,

            "reference_high": None,

            "reference_source": (
                reference_source
            ),
        }

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

    return {
        "unit": unit,

        "reference_low": (
            catalog_low
        ),

        "reference_high": (
            catalog_high
        ),

        "reference_source": (
            "internal_catalog"
            if has_catalog_reference
            else None
        ),
    }


# ============================================================
# PATIENT PROFILE
# ============================================================


def get_patient_profile(
    db: Session,
    user: User,
) -> PatientProfile:
    """
    Возвращает профиль текущего пациента.
    """

    if user.role != "patient":
        raise PatientRoleRequiredError(
            "Patient account required"
        )

    statement = select(
        PatientProfile
    ).where(
        PatientProfile.user_id
        == user.id
    )

    profile = db.scalar(
        statement
    )

    if profile is None:
        raise PatientProfileNotFoundError(
            "Patient profile not found"
        )

    return profile


# ============================================================
# LAB VALUES
# ============================================================


def save_lab_values(
    db: Session,
    *,
    screening_id: str,
    features: dict,
    lab_metadata: dict | None = None,
    reference_source: str | None = None,
) -> None:
    """
    Сохраняет лабораторные показатели
    для истории и будущих графиков.

    Дополнительно сохраняет:
    - unit
    - reference_low
    - reference_high
    - reference_source

    Если metadata отсутствуют,
    используется безопасный backend fallback.
    """

    ignored_features = {
        "sex",
        "age_years",
    }

    lab_metadata = (
        lab_metadata
        or {}
    )

    for feature, value in features.items():

        if feature in ignored_features:
            continue

        if value is None:
            continue

        try:
            numeric_value = float(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        metadata = lab_metadata.get(
            feature,
            {},
        )

        resolved_metadata = (
            resolve_lab_metadata(
                feature=feature,
                metadata=metadata,
                reference_source=(
                    reference_source
                ),
            )
        )

        lab_value = LabValue(
            screening_id=screening_id,

            feature=feature,

            value=numeric_value,

            unit=(
                resolved_metadata[
                    "unit"
                ]
            ),

            reference_low=(
                resolved_metadata[
                    "reference_low"
                ]
            ),

            reference_high=(
                resolved_metadata[
                    "reference_high"
                ]
            ),

            reference_source=(
                resolved_metadata[
                    "reference_source"
                ]
            ),
        )

        db.add(
            lab_value
        )


# ============================================================
# SAVE SCREENING
# ============================================================


def save_screening(
    db: Session,
    *,
    user: User,
    patient_profile: PatientProfile,
    features: dict,
    result: dict,
    lab_metadata: dict | None = None,
    source_type: str = "manual",
    source_filename: str | None = None,
) -> Screening:
    """
    Сохраняет результат уже выполненного screening.

    ML здесь не вызывается.

    lab_metadata используется только для
    сохранения единиц и референсных диапазонов.
    """

    screening_id = result[
        "screening_id"
    ]

    data_quality = result.get(
        "data_quality",
        {},
    )

    model = result.get(
        "model",
        {},
    )

    screening = Screening(
        id=screening_id,

        patient_profile_id=(
            patient_profile.id
        ),

        created_by_user_id=(
            user.id
        ),

        source_type=source_type,

        source_filename=(
            source_filename
        ),

        input_data=features,

        result_data=result,

        coverage=data_quality.get(
            "coverage"
        ),

        bundle_name=model.get(
            "bundle_name"
        ),

        bundle_version=model.get(
            "bundle_version"
        ),
    )

    # ========================================================
    # REFERENCE SOURCE
    # ========================================================

    if source_type == "file":
        reference_source = "lab_file"

    else:
        reference_source = "manual"

    # ========================================================
    # DATABASE
    # ========================================================

    try:
        db.add(
            screening
        )

        # Сначала записываем Screening
        # в текущую транзакцию.
        #
        # Иначе LabValue не сможет
        # сослаться на screening_id.
        db.flush()

        save_lab_values(
            db,
            screening_id=screening_id,
            features=features,
            lab_metadata=lab_metadata,
            reference_source=reference_source,
        )

        db.commit()

        db.refresh(
            screening
        )

    except Exception:
        db.rollback()
        raise

    return screening


# ============================================================
# HISTORY
# ============================================================


def get_screening_history(
    db: Session,
    *,
    patient_profile: PatientProfile,
) -> list[Screening]:
    """
    Возвращает историю от новых результатов
    к старым.
    """

    statement = (
        select(
            Screening
        )
        .where(
            Screening.patient_profile_id
            == patient_profile.id
        )
        .order_by(
            Screening.created_at.desc()
        )
    )

    return list(
        db.scalars(
            statement
        ).all()
    )


def get_screening_by_id(
    db: Session,
    *,
    patient_profile: PatientProfile,
    screening_id: str,
) -> Screening:
    """
    Получение результата только если он
    принадлежит текущему пациенту.
    """

    statement = select(
        Screening
    ).where(
        Screening.id
        == screening_id,

        Screening.patient_profile_id
        == patient_profile.id,
    )

    screening = db.scalar(
        statement
    )

    if screening is None:
        raise ScreeningNotFoundError(
            "Screening not found"
        )

    return screening


def delete_screening(
    db: Session,
    *,
    patient_profile: PatientProfile,
    screening_id: str,
) -> None:

    screening = get_screening_by_id(
        db,
        patient_profile=patient_profile,
        screening_id=screening_id,
    )

    try:
        # На SQLite foreign key CASCADE уже
        # включён в database.py.
        db.delete(
            screening
        )

        db.commit()

    except Exception:
        db.rollback()
        raise
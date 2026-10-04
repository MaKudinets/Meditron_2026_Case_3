from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import (
    LabValue,
    PatientProfile,
    Screening,
    User,
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

        unit = metadata.get(
            "unit"
        )

        reference_low = metadata.get(
            "reference_low"
        )

        reference_high = metadata.get(
            "reference_high"
        )

        lab_value = LabValue(
            screening_id=screening_id,

            feature=feature,

            value=numeric_value,

            unit=unit,

            reference_low=(
                reference_low
            ),

            reference_high=(
                reference_high
            ),

            reference_source=(
                reference_source
                if metadata
                else None
            ),
        )

        db.add(
            lab_value
        )


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
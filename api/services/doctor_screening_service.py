from sqlalchemy import select

from sqlalchemy.orm import Session

from api.database.models import (
    DoctorPatientAccess,
    PatientProfile,
    User,
)

from api.schemas.doctor_screenings import (
    DoctorBulkScreeningPatient,
)

from api.schemas.response import (
    ScreeningResponse,
)

from api.services.history_service import (
    save_screening,
)

from api.services.screening_service import (
    run_screening,
)


class DoctorRoleRequiredError(
    ValueError
):
    pass


# ============================================================
# INTERNAL PATIENT CODE
# ============================================================


def build_internal_patient_code(
    doctor: User,
    patient_code: str,
) -> str:
    """
    Делает код пациента уникальным
    в рамках конкретного врача.

    Например:

    врач A + P-001
    врач B + P-001

    не должны случайно превратиться
    в одного пациента.
    """

    clean_code = (
        patient_code.strip()
    )

    return (
        f"{doctor.id}:{clean_code}"
    )


# ============================================================
# GET / CREATE PATIENT
# ============================================================


def get_or_create_doctor_patient(
    db: Session,
    *,
    doctor: User,
    patient_code: str,
) -> PatientProfile:
    """
    Находит существующего пациента врача
    либо создаёт новый PatientProfile.

    Для пациента, добавленного врачом,
    User создавать не требуется.
    """

    if doctor.role != "doctor":

        raise DoctorRoleRequiredError(
            "Doctor account required"
        )

    internal_code = (
        build_internal_patient_code(
            doctor,
            patient_code,
        )
    )

    # ========================================================
    # PROFILE
    # ========================================================

    profile = db.scalar(
        select(
            PatientProfile
        ).where(
            PatientProfile.external_code
            == internal_code
        )
    )

    try:

        if profile is None:

            profile = PatientProfile(
                external_code=(
                    internal_code
                ),
            )

            db.add(
                profile
            )

            # Нужен ID профиля для
            # DoctorPatientAccess.
            db.flush()

        # ====================================================
        # DOCTOR ACCESS
        # ====================================================

        access = db.scalar(
            select(
                DoctorPatientAccess
            ).where(
                DoctorPatientAccess.doctor_user_id
                == doctor.id,

                DoctorPatientAccess.patient_profile_id
                == profile.id,
            )
        )

        if access is None:

            access = (
                DoctorPatientAccess(
                    doctor_user_id=(
                        doctor.id
                    ),

                    patient_profile_id=(
                        profile.id
                    ),
                )
            )

            db.add(
                access
            )

        # Сохраняем профиль и связь
        # независимо от дальнейшего ML.
        db.commit()

        db.refresh(
            profile
        )

    except Exception:

        db.rollback()

        raise

    return profile


# ============================================================
# ONE PATIENT SCREENING
# ============================================================


def run_doctor_patient_screening(
    db: Session,
    *,
    doctor: User,
    patient: DoctorBulkScreeningPatient,
    source_filename: str | None,
) -> ScreeningResponse:
    """
    Запускает screening одного
    подтвержденного врачом пациента.

    Существующий ML НЕ изменяется.
    """

    # ========================================================
    # PATIENT PROFILE
    # ========================================================

    patient_profile = (
        get_or_create_doctor_patient(
            db,
            doctor=doctor,
            patient_code=(
                patient.patient_code
            ),
        )
    )

    # ========================================================
    # FEATURES
    # ========================================================

    features = (
        patient.features.model_dump(
            exclude_none=True,
            mode="json",
        )
    )

    # ========================================================
    # LAB METADATA
    # ========================================================

    lab_metadata = {}

    for feature, metadata in (
        patient.lab_metadata.items()
    ):

        if feature not in features:
            continue

        lab_metadata[
            feature
        ] = metadata.model_dump(
            mode="json"
        )

    # ========================================================
    # EXISTING ML
    # ========================================================

    result = run_screening(
        features=features,

        patient_id=(
            patient_profile.id
        ),
    )

    response = ScreeningResponse(
        **result
    )

    result_for_storage = (
        response.model_dump(
            mode="json"
        )
    )

    # ========================================================
    # HISTORY
    # ========================================================

    save_screening(
        db,

        # created_by_user_id будет врачом.
        user=doctor,

        patient_profile=(
            patient_profile
        ),

        features=features,

        result=(
            result_for_storage
        ),

        lab_metadata=(
            lab_metadata
        ),

        source_type="file",

        source_filename=(
            source_filename
        ),
    )

    return response
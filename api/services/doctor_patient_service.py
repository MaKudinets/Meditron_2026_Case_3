from sqlalchemy import (
    func,
    select,
)

from sqlalchemy.orm import Session

from api.database.models import (
    DoctorPatientAccess,
    PatientProfile,
    Screening,
    User,
)

from api.services.doctor_screening_service import (
    build_internal_patient_code,
)


class DoctorRoleRequiredError(
    ValueError
):
    pass


class DoctorPatientNotFoundError(
    ValueError
):
    pass


class DoctorScreeningNotFoundError(
    ValueError
):
    pass


# ============================================================
# ROLE
# ============================================================


def require_doctor(
    doctor: User,
) -> None:
    """
    Проверяет роль пользователя.
    """

    if doctor.role != "doctor":

        raise DoctorRoleRequiredError(
            "Doctor account required"
        )


# ============================================================
# DISPLAY PATIENT CODE
# ============================================================


def get_display_patient_code(
    profile: PatientProfile,
) -> str:
    """
    В БД external_code хранится примерно так:

    doctor_uuid:P-001

    Во frontend врачу показываем только:

    P-001
    """

    external_code = (
        profile.external_code
        or ""
    )

    if ":" in external_code:

        return external_code.split(
            ":",
            1,
        )[1]

    return external_code


# ============================================================
# GET DOCTOR PATIENT
# ============================================================


def get_doctor_patient(
    db: Session,
    *,
    doctor: User,
    patient_code: str,
) -> PatientProfile:
    """
    Возвращает пациента только в том случае,
    если он связан с текущим врачом.

    Это не позволяет одному врачу открыть
    пациента другого врача.
    """

    require_doctor(
        doctor
    )

    internal_code = (
        build_internal_patient_code(
            doctor,
            patient_code,
        )
    )

    statement = (
        select(
            PatientProfile
        )
        .join(
            DoctorPatientAccess,
            (
                DoctorPatientAccess.patient_profile_id
                == PatientProfile.id
            ),
        )
        .where(
            DoctorPatientAccess.doctor_user_id
            == doctor.id,

            PatientProfile.external_code
            == internal_code,
        )
    )

    profile = db.scalar(
        statement
    )

    if profile is None:

        raise DoctorPatientNotFoundError(
            "Patient not found"
        )

    return profile


# ============================================================
# LIST DOCTOR PATIENTS
# ============================================================


def list_doctor_patients(
    db: Session,
    *,
    doctor: User,
) -> list[dict]:
    """
    Возвращает пациентов текущего врача
    вместе с количеством исследований
    и датой последнего.
    """

    require_doctor(
        doctor
    )

    statement = (
        select(
            PatientProfile
        )
        .join(
            DoctorPatientAccess,
            (
                DoctorPatientAccess.patient_profile_id
                == PatientProfile.id
            ),
        )
        .where(
            DoctorPatientAccess.doctor_user_id
            == doctor.id
        )
        .order_by(
            PatientProfile.external_code.asc()
        )
    )

    profiles = list(
        db.scalars(
            statement
        ).all()
    )

    result = []

    for profile in profiles:

        stats_statement = (
            select(
                func.count(
                    Screening.id
                ),
                func.max(
                    Screening.created_at
                ),
            )
            .where(
                Screening.patient_profile_id
                == profile.id
            )
        )

        (
            screening_count,
            last_screening_at,
        ) = db.execute(
            stats_statement
        ).one()

        result.append({
            "patient_code": (
                get_display_patient_code(
                    profile
                )
            ),

            "screening_count": int(
                screening_count
                or 0
            ),

            "last_screening_at": (
                last_screening_at
            ),
        })

    return result


# ============================================================
# PATIENT SCREENING HISTORY
# ============================================================


def list_doctor_patient_screenings(
    db: Session,
    *,
    doctor: User,
    patient_code: str,
) -> list[Screening]:
    """
    История одного пациента текущего врача.
    """

    profile = get_doctor_patient(
        db,
        doctor=doctor,
        patient_code=patient_code,
    )

    statement = (
        select(
            Screening
        )
        .where(
            Screening.patient_profile_id
            == profile.id
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


# ============================================================
# ONE SCREENING
# ============================================================


def get_doctor_patient_screening(
    db: Session,
    *,
    doctor: User,
    patient_code: str,
    screening_id: str,
) -> Screening:
    """
    Получает конкретный screening.

    Проверяется одновременно:
    - врач
    - пациент
    - screening_id
    """

    profile = get_doctor_patient(
        db,
        doctor=doctor,
        patient_code=patient_code,
    )

    statement = (
        select(
            Screening
        )
        .where(
            Screening.id
            == screening_id,

            Screening.patient_profile_id
            == profile.id,
        )
    )

    screening = db.scalar(
        statement
    )

    if screening is None:

        raise DoctorScreeningNotFoundError(
            "Screening not found"
        )

    return screening
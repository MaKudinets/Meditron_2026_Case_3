from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from api.database.database import Base


def generate_id() -> str:
    return uuid4().hex


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# USERS
# ============================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # patient / doctor
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="patient",
    )

    is_email_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# PATIENT PROFILES
# ============================================================

class PatientProfile(Base):
    """
    Профиль пациента.

    user_id заполнен, если пациент имеет собственный аккаунт.

    Для пациентов, добавленных врачом, user_id может быть NULL,
    а вместо него используется обезличенный external_code.
    """

    __tablename__ = "patient_profiles"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    user_id: Mapped[str | None] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=True,
        index=True,
    )

    external_code: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# DOCTOR -> PATIENT ACCESS
# ============================================================

class DoctorPatientAccess(Base):
    __tablename__ = "doctor_patient_access"

    doctor_user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    patient_profile_id: Mapped[str] = mapped_column(
        ForeignKey(
            "patient_profiles.id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )


# ============================================================
# AUTH SESSIONS
# ============================================================

class AuthSession(Base):
    """
    Серверная сессия пользователя.

    Она нужна в том числе для настоящего logout.
    """

    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================================
# EMAIL VERIFICATION
# ============================================================

class EmailVerificationToken(Base):
    __tablename__ = "email_verification_tokens"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================================
# PASSWORD RESET
# ============================================================

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================================
# SCREENINGS
# ============================================================

class Screening(Base):
    __tablename__ = "screenings"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    patient_profile_id: Mapped[str] = mapped_column(
        ForeignKey(
            "patient_profiles.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_by_user_id: Mapped[str] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        index=True,
    )

    # manual / file
    source_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="manual",
    )

    source_filename: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Что реально было подано на ML
    input_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    # Полный ответ нашего API
    result_data: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    coverage: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    bundle_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    bundle_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )


# ============================================================
# LAB VALUES
# ============================================================

class LabValue(Base):
    __tablename__ = "lab_values"

    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=generate_id,
    )

    screening_id: Mapped[str] = mapped_column(
        ForeignKey(
            "screenings.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    feature: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    reference_low: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    reference_high: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # lab_file / internal_catalog / manual
    reference_source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
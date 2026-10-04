from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.models import (
    LabValue,
    PatientProfile,
    Screening,
)

from api.resources.lab_groups import (
    FEATURE_LABELS,
    LAB_GROUPS,
)


def _same_value_or_none(
    values: list,
):
    """
    Возвращает значение, если оно одинаково
    во всех непустых точках.
    """

    filtered = [
        value
        for value in values
        if value is not None
    ]

    if not filtered:
        return None

    first = filtered[0]

    if all(
        value == first
        for value in filtered
    ):
        return first

    return None


def get_patient_trends(
    db: Session,
    *,
    patient_profile: PatientProfile,
) -> dict:

    statement = (
        select(
            LabValue,
            Screening.created_at,
        )
        .join(
            Screening,
            LabValue.screening_id
            == Screening.id,
        )
        .where(
            Screening.patient_profile_id
            == patient_profile.id
        )
        .order_by(
            Screening.created_at.asc()
        )
    )

    rows = db.execute(
        statement
    ).all()

    feature_values = {}

    for lab_value, created_at in rows:

        feature_values.setdefault(
            lab_value.feature,
            [],
        )

        feature_values[
            lab_value.feature
        ].append({
            "screening_id": (
                lab_value.screening_id
            ),

            "date": created_at,

            "value": (
                lab_value.value
            ),

            "unit": (
                lab_value.unit
            ),

            "reference_low": (
                lab_value.reference_low
            ),

            "reference_high": (
                lab_value.reference_high
            ),

            "reference_source": (
                lab_value.reference_source
            ),
        })

    groups = []

    for group_key, group_config in (
        LAB_GROUPS.items()
    ):

        series = []

        for feature in group_config[
            "features"
        ]:

            values = feature_values.get(
                feature,
                [],
            )

            if not values:
                continue

            unit = _same_value_or_none(
                [
                    item["unit"]
                    for item in values
                ]
            )

            reference_low = (
                _same_value_or_none(
                    [
                        item[
                            "reference_low"
                        ]
                        for item in values
                    ]
                )
            )

            reference_high = (
                _same_value_or_none(
                    [
                        item[
                            "reference_high"
                        ]
                        for item in values
                    ]
                )
            )

            points = []

            for item in values:

                points.append({
                    "screening_id": (
                        item[
                            "screening_id"
                        ]
                    ),

                    "date": item[
                        "date"
                    ],

                    "value": item[
                        "value"
                    ],

                    "reference_low": item[
                        "reference_low"
                    ],

                    "reference_high": item[
                        "reference_high"
                    ],

                    "reference_source": item[
                        "reference_source"
                    ],
                })

            series.append({
                "feature": feature,

                "label": (
                    FEATURE_LABELS.get(
                        feature,
                        feature,
                    )
                ),

                "unit": unit,

                "reference_low": (
                    reference_low
                ),

                "reference_high": (
                    reference_high
                ),

                "points": points,
            })

        if series:

            groups.append({
                "key": group_key,

                "label": (
                    group_config[
                        "label"
                    ]
                ),

                "series": series,
            })

    return {
        "groups": groups
    }
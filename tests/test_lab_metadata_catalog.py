from api.resources.lab_catalog import (
    get_lab_catalog_metadata,
)

from api.services.history_service import (
    resolve_lab_metadata,
)


def test_catalog_returns_known_ferritin_metadata():
    metadata = (
        get_lab_catalog_metadata(
            "ferritin"
        )
    )

    assert (
        metadata["unit"]
        == "нг/мл"
    )

    assert (
        metadata["reference_low"]
        == 15.0
    )

    assert (
        metadata["reference_high"]
        == 150.0
    )


def test_catalog_returns_empty_for_unknown_feature():
    metadata = (
        get_lab_catalog_metadata(
            "unknown_feature"
        )
    )

    assert metadata == {}


def test_fallback_uses_internal_catalog():
    metadata = (
        resolve_lab_metadata(
            feature="ferritin",
            metadata={},
            reference_source="manual",
        )
    )

    assert (
        metadata["unit"]
        == "нг/мл"
    )

    assert (
        metadata["reference_low"]
        == 15.0
    )

    assert (
        metadata["reference_high"]
        == 150.0
    )

    assert (
        metadata["reference_source"]
        == "internal_catalog"
    )


def test_lab_metadata_has_priority_over_catalog():
    metadata = (
        resolve_lab_metadata(
            feature="ferritin",

            metadata={
                "unit": "custom-unit",
                "reference_low": 20.0,
                "reference_high": 200.0,
            },

            reference_source=(
                "lab_file"
            ),
        )
    )

    assert (
        metadata["unit"]
        == "custom-unit"
    )

    assert (
        metadata["reference_low"]
        == 20.0
    )

    assert (
        metadata["reference_high"]
        == 200.0
    )

    assert (
        metadata["reference_source"]
        == "lab_file"
    )


def test_catalog_can_fill_missing_unit():
    metadata = (
        resolve_lab_metadata(
            feature="ferritin",

            metadata={
                "reference_low": 20.0,
                "reference_high": 200.0,
            },

            reference_source=(
                "lab_file"
            ),
        )
    )

    assert (
        metadata["unit"]
        == "нг/мл"
    )

    assert (
        metadata["reference_low"]
        == 20.0
    )

    assert (
        metadata["reference_high"]
        == 200.0
    )

    assert (
        metadata["reference_source"]
        == "lab_file"
    )


def test_reference_text_blocks_catalog_reference():
    metadata = (
        resolve_lab_metadata(
            feature="ferritin",

            metadata={
                "unit": "нг/мл",
                "reference_text": (
                    "лабораторный диапазон"
                ),
            },

            reference_source=(
                "lab_file"
            ),
        )
    )

    assert (
        metadata["unit"]
        == "нг/мл"
    )

    assert (
        metadata["reference_low"]
        is None
    )

    assert (
        metadata["reference_high"]
        is None
    )

    assert (
        metadata["reference_source"]
        == "lab_file"
    )


def test_unit_only_catalog_feature_has_no_fake_reference():
    metadata = (
        resolve_lab_metadata(
            feature="CRP",
            metadata={},
            reference_source="manual",
        )
    )

    assert (
        metadata["unit"]
        == "мг/л"
    )

    assert (
        metadata["reference_low"]
        is None
    )

    assert (
        metadata["reference_high"]
        is None
    )

    assert (
        metadata["reference_source"]
        is None
    )


def test_unknown_feature_stays_empty():
    metadata = (
        resolve_lab_metadata(
            feature="unknown_feature",
            metadata={},
            reference_source="manual",
        )
    )

    assert (
        metadata["unit"]
        is None
    )

    assert (
        metadata["reference_low"]
        is None
    )

    assert (
        metadata["reference_high"]
        is None
    )

    assert (
        metadata["reference_source"]
        is None
    )
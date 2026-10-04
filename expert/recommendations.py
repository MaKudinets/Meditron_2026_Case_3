from __future__ import annotations

from typing import Dict, List, Any
import pandas as pd

from expert.knowledge_base import (
    PHYSICIAN_PANELS,
    assess_hypothesis_completeness,
)


def recommended_next_tests(
    row: pd.Series,
    probabilities: Dict[str, float],
    probability_threshold: float = 0.50,
) -> List[Dict[str, str]]:
    """
    Формирует рекомендации по дополнительным исследованиям.

    Принципы:
    - missing != normal;
    - рекомендации появляются только при достаточно вероятной ML-гипотезе;
    - сначала рекомендуются отсутствующие ключевые показатели врача;
    - затем полезные supporting markers;
    - это рекомендации по уточнению диагностики, а не лечение.
    """

    suggestions: List[Dict[str, str]] = []

    def add_if_missing(
        feature: str,
        target: str,
        priority: str,
        reason: str,
    ) -> None:
        if feature not in row.index or pd.isna(row.get(feature)):
            suggestions.append({
                "test": feature,
                "target": target,
                "priority": priority,
                "reason": reason,
            })

    for target, panel in PHYSICIAN_PANELS.items():

        probability = float(probabilities.get(target, 0.0))

        if probability < probability_threshold:
            continue

        completeness = assess_hypothesis_completeness(
            row=row,
            target=target,
        )

        # 1. Ключевые показатели врача
        for feature in completeness["missing_key_markers"]:
            add_if_missing(
                feature=feature,
                target=target,
                priority="key",
                reason=(
                    f"Отсутствует ключевой показатель для полной "
                    f"проверки гипотезы {target}. "
                    f"По доступным данным гипотеза требует уточнения."
                ),
            )

        # 2. Supporting markers
        for feature in completeness["missing_supporting_markers"]:
            add_if_missing(
                feature=feature,
                target=target,
                priority="supporting",
                reason=(
                    f"Дополнительный показатель может помочь "
                    f"уточнить гипотезу {target}."
                ),
            )

    return suggestions


def build_recommendation_events(
    run_id: str,
    row: pd.Series,
    probabilities: Dict[str, float],
    probability_threshold: float = 0.50,
) -> List[Dict[str, Any]]:
    """
    Формирует события для Durable Rules engine.

    recommended_next_tests() определяет,
    какие отсутствующие исследования стоит рекомендовать.

    Здесь мы добавляем технические поля,
    необходимые Durable Rules:
    - run_id
    - kind
    - missing
    - probability
    """

    recommendations = recommended_next_tests(
        row=row,
        probabilities=probabilities,
        probability_threshold=probability_threshold,
    )

    events: List[Dict[str, Any]] = []

    for recommendation in recommendations:

        target = recommendation["target"]

        events.append({
            "run_id": run_id,
            "kind": "recommendation",

            "test": recommendation["test"],
            "target": target,

            "reason": recommendation["reason"],
            "priority": recommendation.get(
                "priority",
                "supporting",
            ),

            # Эти два поля нужны Durable Rules.
            "missing": True,
            "probability": float(
                probabilities.get(target, 0.0)
            ),
        })

    return events
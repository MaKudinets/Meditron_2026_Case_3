import json
from pathlib import Path

import torch
from catboost import CatBoostClassifier

from ml.training.train_labs import TabularMLP


# БАЗОВЫЕ ПУТИ


PROJECT_ROOT = Path(
    __file__
).resolve().parents[2]

ML_DIR = (
    PROJECT_ROOT
    / "ml"
)

ARTIFACTS_DIR = (
    ML_DIR
    / "artifacts"
)



# ЗАГРУЗКА METRICS.JSON

def load_metrics(
    task,
    model_type
):
    """
    Загружает metrics.json
    для выбранной задачи и модели.
    """

    metrics_path = (
        ARTIFACTS_DIR
        / task
        / model_type
        / "metrics.json"
    )


    if not metrics_path.exists():

        raise FileNotFoundError(
            f"Metrics not found: {metrics_path}"
        )


    with open(
        metrics_path,
        "r",
        encoding="utf-8"
    ) as file:

        metrics = json.load(
            file
        )


    return metrics


# ЗАГРУЗКА CATBOOST


def load_catboost_model(
    task
):
    """
    Загружает CatBoost-модель
    для выбранной задачи.
    """

    model_path = (
        ARTIFACTS_DIR
        / task
        / "catboost"
        / "model.cbm"
    )


    if not model_path.exists():

        raise FileNotFoundError(
            f"CatBoost model not found: {model_path}"
        )


    model = CatBoostClassifier()


    model.load_model(
        model_path
    )


    return model


# ЗАГРУЗКА MLP


def load_mlp_model(
    task
):
    """
    Загружает PyTorch MLP
    для выбранной задачи.
    """

    model_path = (
        ARTIFACTS_DIR
        / task
        / "mlp"
        / "model.pt"
    )


    if not model_path.exists():

        raise FileNotFoundError(
            f"MLP model not found: {model_path}"
        )


    checkpoint = torch.load(
        model_path,
        map_location="cpu",
        weights_only=False
    )


    model = TabularMLP(

        input_dim=checkpoint[
            "input_dim"
        ],

        hidden_1=checkpoint[
            "hidden_1"
        ],

        hidden_2=checkpoint[
            "hidden_2"
        ],

        dropout=checkpoint[
            "dropout"
        ]
    )


    model.load_state_dict(
        checkpoint[
            "state_dict"
        ]
    )


    model.eval()


    return (
        model,
        checkpoint
    )



# УНИВЕРСАЛЬНАЯ ЗАГРУЗКА


def load_model(
    task,
    model_type
):
    """
    Единая функция загрузки модели.

    task:
        vitamin_d
        iron

    model_type:
        catboost
        mlp
    """

    if task not in {
        "vitamin_d",
        "iron"
    }:

        raise ValueError(
            f"Unknown task: {task}"
        )



    # CATBOOST


    if model_type == "catboost":

        model = load_catboost_model(
            task
        )

        metrics = load_metrics(
            task,
            "catboost"
        )


        return {
            "task": task,

            "model_type": (
                "catboost"
            ),

            "model": model,

            "threshold": (
                metrics[
                    "threshold"
                ]
            ),

            "metrics": metrics
        }


    # MLP


    if model_type == "mlp":

        model, checkpoint = (
            load_mlp_model(
                task
            )
        )

        metrics = load_metrics(
            task,
            "mlp"
        )


        return {
            "task": task,

            "model_type": (
                "mlp"
            ),

            "model": model,

            "checkpoint": (
                checkpoint
            ),

            "threshold": (
                metrics[
                    "threshold"
                ]
            ),

            "metrics": metrics
        }


    raise ValueError(
        f"Unknown model_type: {model_type}"
    )
import pandas as pd
import torch

from ml.inference.model_loader import load_model
from ml.preprocessing.labs import prepare_features


def predict(
    dataframe,
    task,
    model_type,
    rename_map=None,
    min_feature_coverage=0.70,
):
    """
    Единая функция inference
    для CatBoost и MLP.
    """


    # 1. ЗАГРУЖАЕМ МОДЕЛЬ


    bundle = load_model(
        task=task,
        model_type=model_type,
    )

    model = bundle["model"]
    threshold = bundle["threshold"]


    # 2. ГОТОВИМ ПРИЗНАКИ


    X, report = prepare_features(
        dataframe=dataframe,
        task=task,
        model_type=model_type,
        rename_map=rename_map,
    )


    # 3. ПРОВЕРЯЕМ ДОСТАТОЧНОСТЬ ДАННЫХ


    if (
        report["feature_coverage"]
        < min_feature_coverage
    ):

        result = pd.DataFrame({
            "probability": [
                0.0
                for _ in range(len(dataframe))
            ],
            "threshold": [
                threshold
                for _ in range(len(dataframe))
            ],
            "screen_positive": [
                False
                for _ in range(len(dataframe))
            ],
            "status": [
                "insufficient_data"
                for _ in range(len(dataframe))
            ],
        })

        return (
            result,
            report
        )


    # 4. ПРЕДСКАЗАНИЕ


    if model_type == "catboost":

        probabilities = (
            model.predict_proba(
                X
            )[:, 1]
        )


    elif model_type == "mlp":

        tensor = torch.tensor(
            X,
            dtype=torch.float32,
        )

        model.eval()

        with torch.no_grad():

            logits = model(
                tensor
            )

            probabilities = (
                torch.sigmoid(
                    logits
                )
                .cpu()
                .numpy()
                .reshape(-1)
            )


    else:

        raise ValueError(
            f"Unknown model_type: {model_type}"
        )


    # 5. ПРЕВРАЩАЕМ В 0 / 1


    predictions = (
        probabilities >= threshold
    ).astype(int)


    # 6. СТАТУС


    statuses = [
        (
            "elevated_screening_risk"
            if prediction == 1
            else "low_screening_risk"
        )
        for prediction in predictions
    ]


    # 7. РЕЗУЛЬТАТ


    result = pd.DataFrame({
        "probability": (probabilities),
        "threshold": (threshold),
        "screen_positive": (predictions.astype(bool)),
        "status": (statuses),
    })


    return (
        result,
        report
    )
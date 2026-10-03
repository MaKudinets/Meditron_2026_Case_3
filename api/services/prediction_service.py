import pandas as pd
from ml.inference.predictor import predict

def _format_prediction(result):
    """
    Преобразует результат ML-predictor из DataFrame
    в обычный Python-словарь для API.
    """

    row = result.iloc[0]

    return {
        "probability": float(row["probability"]),
        "threshold": float(row["threshold"]),
        "screen_positive": bool(row["screen_positive"]),
        "status": str(row["status"]),
    }


def get_prediction(features):
    """
    Выполняет предсказание Vitamin D и Iron
    для одного пациента.
    """

    # 1. Превращаем признаки пациента в DataFrame
    patient_df = pd.DataFrame([features])

    # 2. Vitamin D
    vitamin_d_result, vitamin_d_report = predict(
        dataframe=patient_df.copy(),
        task="vitamin_d",
        model_type="mlp",
    )

    # 3. Iron
    iron_result, iron_report = predict(
        dataframe=patient_df.copy(),
        task="iron",
        model_type="catboost",
    )

    # 4. Формируем единый результат
    return {
        "vitamin_d": _format_prediction(vitamin_d_result),
        "iron": _format_prediction(iron_result),
    }
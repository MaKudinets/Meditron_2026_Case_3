import {
  apiRequest,
  cfg,
  ApiError,
} from "./client.js";

import {
  fixture,
  delay,
  addHistory,
} from "../mocks/screening.js";


// ============================================================
// REQUEST
// ============================================================


export function makePayload(
  data,
) {
  const features = {};


  // ----------------------------------------------------------
  // Demographics
  // ----------------------------------------------------------


  if (
    data.age_years !==
    null &&
    data.age_years !==
    undefined &&
    data.age_years !==
    ""
  ) {
    const age =
      Number(
        data.age_years,
      );

    if (
      !Number.isFinite(
        age,
      ) ||
      age < 0 ||
      age > 120
    ) {
      throw new ApiError(
        "Возраст должен быть числом от 0 до 120.",
      );
    }

    features.age_years =
      age;
  }


  if (
    data.sex !== "F" &&
    data.sex !== "M"
  ) {
    throw new ApiError(
      "Укажите пол пациента.",
    );
  }

  features.sex =
    data.sex;


  // ----------------------------------------------------------
  // Laboratory values
  // ----------------------------------------------------------


  for (
    const item
    of data.labs
  ) {
    if (
      item.value ===
        null ||
      item.value ===
        "" ||
      item.value ===
        undefined
    ) {
      continue;
    }


    if (
      !Number.isFinite(
        item.value,
      ) ||
      item.value < 0
    ) {
      throw new ApiError(
        "Лабораторные показатели должны быть неотрицательными числами.",
      );
    }


    features[
      item.code
    ] =
      item.value;
  }


  // ----------------------------------------------------------
  // Required backend fields
  // ----------------------------------------------------------


  if (
    features.hemoglobin ===
      undefined
  ) {
    throw new ApiError(
      "Для скрининга необходимо указать гемоглобин.",
    );
  }


  // ----------------------------------------------------------
  // Final MeScreeningRequest
  // ----------------------------------------------------------


  return {
    features,

    lab_metadata:
      data.lab_metadata ||
      {},

    source_filename:
      data.source_filename ||
      null,
  };
}


// ============================================================
// RESPONSE VALIDATION
// ============================================================


export function validateResult(
  result,
) {
  if (
    !result ||
    typeof result !==
      "object"
  ) {
    throw new ApiError(
      "Сервер вернул некорректный результат скрининга.",
    );
  }


  if (
    typeof result.screening_id !==
      "string"
  ) {
    throw new ApiError(
      "В ответе отсутствует идентификатор скрининга.",
    );
  }


  if (
    !result.prediction ||
    typeof result.prediction !==
      "object"
  ) {
    throw new ApiError(
      "В ответе отсутствует итог скрининга.",
    );
  }


  if (
    typeof result.prediction.anemia !==
      "boolean" ||
    typeof result.prediction.anemia_class !==
      "string" ||
    typeof result.prediction.deficiency_cause !==
      "string"
  ) {
    throw new ApiError(
      "Итог скрининга не соответствует API-схеме.",
    );
  }


  if (
    !result.confidence ||
    !Number.isFinite(
      result.confidence.certainty,
    ) ||
    result.confidence.certainty <
      0 ||
    result.confidence.certainty >
      1
  ) {
    throw new ApiError(
      "Некорректная оценка уверенности модели.",
    );
  }


  if (
    !result.data_quality ||
    !Number.isFinite(
      result.data_quality.coverage,
    )
  ) {
    throw new ApiError(
      "В ответе отсутствует информация о полноте данных.",
    );
  }


  if (
    !result.deficiencies ||
    typeof result.deficiencies !==
      "object"
  ) {
    throw new ApiError(
      "В ответе отсутствуют результаты проверки дефицитов.",
    );
  }


  return result;
}


// ============================================================
// CREATE SCREENING
// ============================================================


export async function createScreening(
  data,
) {
  const payload =
    makePayload(
      data,
    );


  // ----------------------------------------------------------
  // DEMO
  // ----------------------------------------------------------


  if (
    cfg.mode ===
    "demo"
  ) {
    await delay();

    const item = {
      id:
        `demo-${Date.now()}`,

      created_at:
        new Date()
          .toISOString(),

      labs:
        data.labs.filter(
          (
            item,
          ) =>
            item.value !==
            null,
        ),

      result:
        structuredClone(
          fixture,
        ),
    };

    addHistory(
      item,
    );

    return item;
  }


  // ----------------------------------------------------------
  // LIVE BACKEND
  // ----------------------------------------------------------


  const response =
    await apiRequest(
      cfg.endpoints.screenings,
      {
        method:
          "POST",

        body:
          JSON.stringify(
            payload,
          ),
      },
    );


  const result =
    validateResult(
      response,
    );


  return {
    id:
      result.screening_id,

    created_at:
      new Date()
        .toISOString(),

    labs:
      data.labs.filter(
        (
          item,
        ) =>
          item.value !==
          null,
      ),

    result,
  };
}
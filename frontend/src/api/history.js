import {
  apiRequest,
  apiBlob,
  cfg,
  ApiError,
} from "./client.js";

import {
  history,
  delay,
} from "../mocks/screening.js";


// ============================================================
// GET HISTORY
// ============================================================


export async function getHistory() {
  if (
    cfg.mode === "demo"
  ) {
    await delay();

    return history;
  }


  const data =
    await apiRequest(
      cfg.endpoints.history,
    );


  const items =
    data?.items;


  if (
    !Array.isArray(
      items,
    )
  ) {
    throw new ApiError(
      "История анализов имеет неожиданный формат.",
    );
  }


  return items;
}


// ============================================================
// GET ONE SCREENING
// ============================================================


export async function getScreening(
  screeningId,
) {
  if (
    !screeningId
  ) {
    throw new ApiError(
      "Не указан идентификатор скрининга.",
    );
  }


  if (
    cfg.mode === "demo"
  ) {
    await delay();

    const item =
      history.find(
        (
          entry,
        ) =>
          entry.id ===
          screeningId ||
          entry.screening_id ===
          screeningId,
      );


    if (
      !item
    ) {
      throw new ApiError(
        "Скрининг не найден.",
        404,
      );
    }


    return (
      item.result ||
      item
    );
  }


  return apiRequest(
    `${cfg.endpoints.history}/${encodeURIComponent(
      screeningId,
    )}`,
  );
}


// ============================================================
// DELETE SCREENING
// ============================================================


export async function deleteScreening(
  screeningId,
) {
  if (
    !screeningId
  ) {
    throw new ApiError(
      "Не указан идентификатор скрининга.",
    );
  }


  if (
    cfg.mode === "demo"
  ) {
    throw new ApiError(
      "Удаление отдельных записей в демонстрационном режиме не подключено.",
    );
  }


  return apiRequest(
    `${cfg.endpoints.history}/${encodeURIComponent(
      screeningId,
    )}`,
    {
      method:
        "DELETE",
    },
  );
}


// ============================================================
// PDF REPORT
// ============================================================


export async function getScreeningPdf(
  screeningId,
) {
  if (
    !screeningId
  ) {
    throw new ApiError(
      "Не указан идентификатор скрининга.",
    );
  }


  if (
    cfg.mode === "demo"
  ) {
    throw new ApiError(
      "Серверный PDF недоступен в демонстрационном режиме.",
    );
  }


  return apiBlob(
    `${cfg.endpoints.history}/${encodeURIComponent(
      screeningId,
    )}/report.pdf`,
  );
}


// ============================================================
// DOWNLOAD PDF
// ============================================================


export async function downloadScreeningPdf(
  screeningId,
) {
  const {
    blob,
    filename,
  } =
    await getScreeningPdf(
      screeningId,
    );


  const objectUrl =
    URL.createObjectURL(
      blob,
    );


  const link =
    document.createElement(
      "a",
    );


  link.href =
    objectUrl;


  link.download =
    filename ||
    `meditron-${screeningId}.pdf`;


  document.body
    .appendChild(
      link,
    );


  link.click();


  link.remove();


  setTimeout(
    () => {
      URL.revokeObjectURL(
        objectUrl,
      );
    },
    1000,
  );
}


// ============================================================
// TRENDS
// ============================================================
//
// Пока сохраняем эту функцию,
// чтобы не сломать существующий trendsPage.js.
// Саму страницу динамики переделаем
// на следующем этапе.
// ============================================================


export async function getTrends() {
  if (
    cfg.mode === "demo"
  ) {
    return null;
  }


  return apiRequest(
    cfg.endpoints.trends,
  );
}


// ============================================================
// OLD DOCTOR BATCH COMPATIBILITY
// ============================================================
//
// Пока сохраняем, чтобы текущая doctor.js
// не упала до этапа интеграции врача.
// На врачебном шаге этот код заменим.
// ============================================================


export async function uploadBatch(
  file,
) {
  if (
    !cfg.endpoints.batch
  ) {
    throw new ApiError(
      "Врачебный пакетный импорт будет подключён на отдельном этапе.",
    );
  }


  const data =
    new FormData();


  data.append(
    "file",
    file,
  );


  return apiRequest(
    cfg.endpoints.batch,
    {
      method:
        "POST",

      body:
        data,
    },
  );
}
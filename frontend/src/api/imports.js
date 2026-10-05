import {
  apiRequest,
  cfg,
  ApiError,
} from "./client.js";


// ============================================================
// PATIENT LAB FILE IMPORT
// ============================================================


export async function importPatientLabFile(
  file,
) {
  if (
    !(file instanceof File)
  ) {
    throw new ApiError(
      "Файл для загрузки не выбран.",
    );
  }


  // Backend ограничивает размер 5 MB.
  const maxSize =
    5 * 1024 * 1024;


  if (
    file.size >
    maxSize
  ) {
    throw new ApiError(
      "Размер файла превышает 5 МБ.",
    );
  }


  const extension =
    file.name
      .split(".")
      .pop()
      ?.toLowerCase();


  const allowed =
    [
      "csv",
      "xlsx",
      "pdf",
    ];


  if (
    !allowed.includes(
      extension,
    )
  ) {
    throw new ApiError(
      "Поддерживаются только CSV, XLSX и PDF.",
    );
  }


  const formData =
    new FormData();


  formData.append(
    "file",
    file,
  );


  const response =
    await apiRequest(
      cfg.endpoints.patientImport,
      {
        method:
          "POST",

        body:
          formData,
      },
    );


  if (
    !response ||
    typeof response !==
      "object"
  ) {
    throw new ApiError(
      "Сервер вернул некорректный ответ при разборе файла.",
    );
  }


  if (
    !response.features ||
    typeof response.features !==
      "object"
  ) {
    throw new ApiError(
      "В ответе импорта отсутствуют распознанные показатели.",
    );
  }


  return response;
}
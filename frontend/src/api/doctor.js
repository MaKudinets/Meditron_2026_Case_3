import {
  apiRequest,
  apiBlob,
  cfg,
  ApiError,
} from "./client.js";


// ============================================================
// HELPERS
// ============================================================


function patientPath(
  patientCode,
) {
  return `${cfg.endpoints.doctorPatients}/${encodeURIComponent(
    patientCode,
  )}`;
}


// ============================================================
// DOCTOR FILE PREVIEW
// ============================================================


export async function importDoctorLabFile(
  file,
) {
  if (
    !(file instanceof File)
  ) {
    throw new ApiError(
      "Файл не выбран.",
    );
  }


  const maxSize =
    10 * 1024 * 1024;


  if (
    file.size >
    maxSize
  ) {
    throw new ApiError(
      "Размер файла превышает 10 МБ.",
    );
  }


  const extension =
    file.name
      .split(".")
      .pop()
      ?.toLowerCase();


  if (
    ![
      "csv",
      "xlsx",
    ].includes(
      extension,
    )
  ) {
    throw new ApiError(
      "Для врача поддерживаются CSV и XLSX.",
    );
  }


  const data =
    new FormData();


  data.append(
    "file",
    file,
  );


  const response =
    await apiRequest(
      cfg.endpoints.doctorImport,
      {
        method:
          "POST",

        body:
          data,
      },
    );


  if (
    !Array.isArray(
      response?.patients,
    )
  ) {
    throw new ApiError(
      "Сервер вернул некорректный preview.",
    );
  }


  return response;
}


// ============================================================
// BULK SCREENING
// ============================================================


export async function runDoctorBulkScreening(
  preview,
  selectedIndexes,
) {
  if (
    !preview
  ) {
    throw new ApiError(
      "Сначала загрузите файл.",
    );
  }


  const patients =
    selectedIndexes
      .map(
        (
          index,
        ) =>
          preview.patients[
            index
          ],
      )
      .filter(
        (
          patient,
        ) =>
          patient &&
          patient.patient_code &&
          !patient
            .missing_required
            ?.length,
      )
      .map(
        (
          patient,
        ) => ({
          patient_code:
            patient.patient_code,

          features:
            patient.features,

          lab_metadata:
            {},
        }),
      );


  if (
    !patients.length
  ) {
    throw new ApiError(
      "Нет пациентов, готовых к скринингу.",
    );
  }


  // Backend разрешает максимум
  // 200 пациентов за один запрос.
  const batchSize =
    200;


  const chunks =
    [];


  for (
    let i = 0;
    i < patients.length;
    i += batchSize
  ) {
    chunks.push(
      patients.slice(
        i,
        i + batchSize,
      ),
    );
  }


  const combined = {
    total:
      0,

    succeeded:
      0,

    failed:
      0,

    results:
      [],
  };


  for (
    const chunk
    of chunks
  ) {
    const response =
      await apiRequest(
        cfg.endpoints
          .doctorBulkScreening,
        {
          method:
            "POST",

          body:
            JSON.stringify({
              source_filename:
                preview.filename ||
                null,

              patients:
                chunk,
            }),
        },
      );


    combined.total +=
      response.total ||
      0;


    combined.succeeded +=
      response.succeeded ||
      0;


    combined.failed +=
      response.failed ||
      0;


    combined.results.push(
      ...(
        response.results ||
        []
      ),
    );
  }


  return combined;
}


// ============================================================
// PATIENT LIST
// ============================================================


export async function getDoctorPatients() {
  const response =
    await apiRequest(
      cfg.endpoints.doctorPatients,
    );


  if (
    !Array.isArray(
      response?.items,
    )
  ) {
    throw new ApiError(
      "Список пациентов имеет неожиданный формат.",
    );
  }


  return response;
}


// ============================================================
// PATIENT HISTORY
// ============================================================


export async function getDoctorPatientHistory(
  patientCode,
) {
  return apiRequest(
    `${patientPath(
      patientCode,
    )}/screenings`,
  );
}


// ============================================================
// ONE SCREENING
// ============================================================


export async function getDoctorPatientScreening(
  patientCode,
  screeningId,
) {
  return apiRequest(
    `${patientPath(
      patientCode,
    )}/screenings/${encodeURIComponent(
      screeningId,
    )}`,
  );
}


// ============================================================
// PATIENT TRENDS
// ============================================================


export async function getDoctorPatientTrends(
  patientCode,
) {
  return apiRequest(
    `${patientPath(
      patientCode,
    )}/trends`,
  );
}


// ============================================================
// PATIENT PDF
// ============================================================


export async function getDoctorPatientPdf(
  patientCode,
  screeningId,
) {
  return apiBlob(
    `${patientPath(
      patientCode,
    )}/screenings/${encodeURIComponent(
      screeningId,
    )}/report.pdf`,
  );
}


// ============================================================
// DOWNLOAD PDF
// ============================================================


export async function downloadDoctorPatientPdf(
  patientCode,
  screeningId,
) {
  const {
    blob,
    filename,
  } =
    await getDoctorPatientPdf(
      patientCode,
      screeningId,
    );


  const url =
    URL.createObjectURL(
      blob,
    );


  const link =
    document.createElement(
      "a",
    );


  link.href =
    url;


  link.download =
    filename ||
    `meditron_${patientCode}_${screeningId}.pdf`;


  document.body
    .appendChild(
      link,
    );


  link.click();


  link.remove();


  setTimeout(
    () => {
      URL.revokeObjectURL(
        url,
      );
    },
    1000,
  );
}
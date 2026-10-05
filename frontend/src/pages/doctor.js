import {
  main,
  esc,
  pct,
  date,
  name,
  errorText,
  page,
  back,
  toast,
} from "../components/index.js";

import {
  currentUser,
} from "../api/auth.js";

import {
  importDoctorLabFile,
  runDoctorBulkScreening,
  getDoctorPatients,
  getDoctorPatientHistory,
  getDoctorPatientScreening,
  getDoctorPatientTrends,
  downloadDoctorPatientPdf,
} from "../api/doctor.js";

import {
  state,
} from "../state.js";


// ============================================================
// LOCAL STATE
// ============================================================


let preview =
  null;


let batchResult =
  null;


let patientList =
  [];


let selectedPatient =
  null;


let selectedHistory =
  null;


let selectedTrends =
  null;


// ============================================================
// HELPERS
// ============================================================


function predictionText(
  prediction,
) {
  if (
    !prediction
  ) {
    return "—";
  }


  return (
    prediction
      .anemia_class ||
    prediction
      .deficiency_cause ||
    "—"
  );
}


function coverageText(
  value,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return pct(
    value,
  );
}


// ============================================================
// MAIN PAGE
// ============================================================


export function doctor() {
  // ----------------------------------------------------------
  // ROLE CHECK
  // ----------------------------------------------------------


  if (
    currentUser &&
    currentUser.role !==
      "doctor"
  ) {
    main.innerHTML =
      page(
        `
        ${back()}

        <div class="empty">

          <h1>
            Кабинет врача
          </h1>

          <p>
            Этот раздел доступен
            только аккаунтам с ролью врача.
          </p>

          <a
            class="btn"
            href="#/profile"
          >
            В личный кабинет →
          </a>

        </div>
        `,
      );

    return;
  }


  renderDoctorPage();


  void loadPatients();
}


// ============================================================
// RENDER ROOT
// ============================================================


function renderDoctorPage() {
  main.innerHTML =
    page(
      `
      ${back()}


      <div class="result-top">

        <div>

          <span class="eyebrow">
            Meditron / врач
          </span>

          <h1>
            Кабинет врача
          </h1>

          <p class="subtitle">
            Пакетный скрининг
            лабораторных данных пациентов
          </p>

        </div>

      </div>


      <!-- ================================================
           IMPORT
      ================================================= -->


      <section class="card">

        <h2>
          1. Загрузите лабораторный файл
        </h2>

        <p>
          Один пациент должен находиться
          в одной строке CSV или XLSX.
          Перед запуском модели Meditron
          покажет preview.
        </p>


        <div class="actions">

          <input
            id="doctor-file"
            type="file"
            accept=".csv,.xlsx"
            hidden
          >


          <button
            class="btn"
            type="button"
            id="doctor-upload"
          >
            ↑ Выбрать CSV / XLSX
          </button>

        </div>


        <div
          id="doctor-import-error"
          role="alert"
        ></div>

      </section>


      <div
        id="doctor-preview"
      ></div>


      <div
        id="doctor-batch-result"
      ></div>


      <!-- ================================================
           PATIENTS
      ================================================= -->


      <section
        style="margin-top:40px"
      >

        <div class="result-top">

          <div>

            <h2>
              Пациенты
            </h2>

            <p class="subtitle">
              Пациенты, для которых
              этот врач уже выполнял
              скрининг
            </p>

          </div>


          <button
            class="btn secondary small"
            id="refresh-patients"
            type="button"
          >
            ↻ Обновить
          </button>

        </div>


        <div
          id="doctor-patients"
        >

          <p role="status">

            <span class="loader"></span>

            Загружаем пациентов…

          </p>

        </div>

      </section>


      <div
        id="doctor-patient-detail"
        style="scroll-margin-top:24px"
      ></div>
      `,
    );


  bindImport();


  document
    .querySelector(
      "#refresh-patients",
    )
    ?.addEventListener(
      "click",
      () =>
        loadPatients(),
    );
}


// ============================================================
// IMPORT
// ============================================================


function bindImport() {
  const input =
    document.querySelector(
      "#doctor-file",
    );


  const button =
    document.querySelector(
      "#doctor-upload",
    );


  button.onclick =
    () =>
      input.click();


  input.addEventListener(
    "change",
    async () => {

      const file =
        input.files?.[0];


      if (
        !file
      ) {
        return;
      }


      const errorBox =
        document.querySelector(
          "#doctor-import-error",
        );


      errorBox.innerHTML =
        "";


      button.disabled =
        true;


      button.innerHTML =
        `
        <span class="loader"></span>
        Разбираем файл…
        `;


      try {
        preview =
          await importDoctorLabFile(
            file,
          );


        batchResult =
          null;


        renderPreview();


        document
          .querySelector(
            "#doctor-batch-result",
          )
          .innerHTML =
            "";


        toast(
          "Файл разобран. Проверьте строки перед запуском.",
        );

      } catch (
        error
      ) {
        errorBox.innerHTML =
          `
          <div class="error">
            ${
              errorText(
                error,
              )
            }
          </div>
          `;

      } finally {
        button.disabled =
          false;


        button.textContent =
          "↑ Выбрать CSV / XLSX";


        input.value =
          "";
      }
    },
  );
}


// ============================================================
// PREVIEW
// ============================================================


function renderPreview() {
  const root =
    document.querySelector(
      "#doctor-preview",
    );


  if (
    !preview
  ) {
    root.innerHTML =
      "";

    return;
  }


  const warnings =
    preview.warnings ||
    [];


  root.innerHTML =
    `
    <section
      class="card"
      style="margin-top:32px"
    >

      <span class="eyebrow">
        Preview файла
      </span>


      <h2
        style="margin-top:14px"
      >
        ${
          esc(
            preview.filename,
          )
        }
      </h2>


      <p>
        Строк в файле:
        <strong>
          ${
            preview.total_rows
          }
        </strong>

        ·

        распознано пациентов:
        <strong>
          ${
            preview.recognized_patients
          }
        </strong>
      </p>


      ${
        warnings.length
          ? `
            <div
              class="notice"
              style="margin-top:18px"
            >

              <div>

                <strong>
                  Предупреждения файла
                </strong>

                <ul>

                  ${
                    warnings
                      .map(
                        (
                          warning,
                        ) => `
                          <li>
                            ${
                              esc(
                                warning,
                              )
                            }
                          </li>
                        `,
                      )
                      .join(
                        "",
                      )
                  }

                </ul>

              </div>

            </div>
          `
          : ""
      }


      <div
        class="table-wrap"
        style="margin-top:24px"
      >

        <table>

          <thead>

            <tr>

              <th>
                ✓
              </th>

              <th>
                Строка
              </th>

              <th>
                Patient code
              </th>

              <th>
                Признаков
              </th>

              <th>
                Проверка
              </th>

            </tr>

          </thead>


          <tbody>

            ${
              preview
                .patients
                .map(
                  (
                    patient,
                    index,
                  ) => {

                    const valid =
                      Boolean(
                        patient
                          .patient_code,
                      ) &&
                      !patient
                        .missing_required
                        ?.length;


                    return `
                      <tr>

                        <td>

                          <input
                            type="checkbox"
                            data-doctor-row="${index}"
                            ${
                              valid
                                ? "checked"
                                : "disabled"
                            }
                          >

                        </td>


                        <td>
                          ${
                            patient
                              .row_number
                          }
                        </td>


                        <td>

                          <strong>
                            ${
                              esc(
                                patient
                                  .patient_code ||
                                "—",
                              )
                            }
                          </strong>

                        </td>


                        <td>
                          ${
                            Object.keys(
                              patient
                                .features ||
                              {},
                            ).length
                          }
                        </td>


                        <td>

                          ${
                            valid
                              ? `
                                <span class="tag">
                                  Готов
                                </span>
                              `
                              : `
                                <span class="tag">
                                  Нужна проверка
                                </span>
                              `
                          }


                          ${
                            patient
                              .missing_required
                              ?.length
                              ? `
                                <p class="hint">

                                  Нет обязательных:
                                  ${
                                    patient
                                      .missing_required
                                      .map(
                                        (
                                          item,
                                        ) =>
                                          esc(
                                            item,
                                          ),
                                      )
                                      .join(
                                        ", ",
                                      )
                                  }

                                </p>
                              `
                              : ""
                          }


                          ${
                            patient
                              .warnings
                              ?.length
                              ? `
                                <ul class="hint">

                                  ${
                                    patient
                                      .warnings
                                      .map(
                                        (
                                          warning,
                                        ) => `
                                          <li>
                                            ${
                                              esc(
                                                warning,
                                              )
                                            }
                                          </li>
                                        `,
                                      )
                                      .join(
                                        "",
                                      )
                                  }

                                </ul>
                              `
                              : ""
                          }

                        </td>

                      </tr>
                    `;
                  },
                )
                .join(
                  "",
                )
            }

          </tbody>

        </table>

      </div>


      <div class="actions">

        <button
          class="btn"
          id="doctor-run-bulk"
          type="button"
        >
          Провести скрининг выбранных →
        </button>

        <button
          class="btn secondary"
          id="doctor-select-all"
          type="button"
        >
          Выбрать все доступные
        </button>

      </div>

    </section>
    `;


  document
    .querySelector(
      "#doctor-select-all",
    )
    .onclick =
      () => {

        document
          .querySelectorAll(
            "[data-doctor-row]:not(:disabled)",
          )
          .forEach(
            (
              checkbox,
            ) => {
              checkbox.checked =
                true;
            },
          );
      };


  document
    .querySelector(
      "#doctor-run-bulk",
    )
    .onclick =
      runBulk;
}


// ============================================================
// RUN BULK
// ============================================================


async function runBulk() {
  const button =
    document.querySelector(
      "#doctor-run-bulk",
    );


  const indexes =
    [
      ...document
        .querySelectorAll(
          "[data-doctor-row]:checked",
        ),
    ].map(
      (
        checkbox,
      ) =>
        Number(
          checkbox.dataset
            .doctorRow,
        ),
    );


  if (
    !indexes.length
  ) {
    toast(
      "Выберите хотя бы одного пациента.",
    );

    return;
  }


  const confirmed =
    window.confirm(
      `Запустить скрининг для ${indexes.length} пациентов?`,
    );


  if (
    !confirmed
  ) {
    return;
  }


  button.disabled =
    true;


  button.innerHTML =
    `
    <span class="loader"></span>
    Выполняем скрининг…
    `;


  try {
    batchResult =
      await runDoctorBulkScreening(
        preview,
        indexes,
      );


    renderBatchResult();


    await loadPatients();


    toast(
      `Обработано: ${batchResult.succeeded} успешно, ${batchResult.failed} с ошибкой.`,
    );

  } catch (
    error
  ) {
    toast(
      error?.message ||
      "Не удалось выполнить пакетный скрининг.",
    );

  } finally {
    button.disabled =
      false;


    button.textContent =
      "Провести скрининг выбранных →";
  }
}


// ============================================================
// BULK RESULT
// ============================================================


function renderBatchResult() {
  const root =
    document.querySelector(
      "#doctor-batch-result",
    );


  if (
    !batchResult
  ) {
    root.innerHTML =
      "";

    return;
  }


  root.innerHTML =
    `
    <section
      class="card"
      style="margin-top:32px"
    >

      <span class="eyebrow">
        Результат пакетного скрининга
      </span>


      <h2
        style="margin-top:14px"
      >
        Обработано
        ${
          batchResult.total
        }
        пациентов
      </h2>


      <p>
        Успешно:
        <strong>
          ${
            batchResult.succeeded
          }
        </strong>

        ·

        ошибок:
        <strong>
          ${
            batchResult.failed
          }
        </strong>
      </p>


      <div
        class="table-wrap"
        style="margin-top:20px"
      >

        <table>

          <thead>

            <tr>

              <th>
                Пациент
              </th>

              <th>
                Статус
              </th>

              <th>
                Результат
              </th>

              <th>
                Полнота
              </th>

            </tr>

          </thead>


          <tbody>

            ${
              batchResult
                .results
                .map(
                  (
                    item,
                  ) => `
                    <tr>

                      <td>
                        ${
                          esc(
                            item
                              .patient_code,
                          )
                        }
                      </td>


                      <td>
                        ${
                          item.status ===
                          "success"
                            ? "✓ Успешно"
                            : "Ошибка"
                        }
                      </td>


                      <td>

                        ${
                          item.prediction
                            ? esc(
                                name(
                                  predictionText(
                                    item
                                      .prediction,
                                  ),
                                ),
                              )
                            : esc(
                                item.error ||
                                "—",
                              )
                        }

                      </td>


                      <td>
                        ${
                          coverageText(
                            item.coverage,
                          )
                        }
                      </td>

                    </tr>
                  `,
                )
                .join(
                  "",
                )
            }

          </tbody>

        </table>

      </div>

    </section>
    `;
}


// ============================================================
// LOAD PATIENTS
// ============================================================


async function loadPatients() {
  const root =
    document.querySelector(
      "#doctor-patients",
    );


  if (
    !root
  ) {
    return;
  }


  root.innerHTML =
    `
    <p role="status">

      <span class="loader"></span>

      Загружаем пациентов…

    </p>
    `;


  try {
    const response =
      await getDoctorPatients();


    patientList =
      response.items;


    renderPatients();

  } catch (
    error
  ) {
    root.innerHTML =
      `
      <div class="error">
        ${
          errorText(
            error,
          )
        }
      </div>
      `;
  }
}


// ============================================================
// PATIENT LIST
// ============================================================


function renderPatients() {
  const root =
    document.querySelector(
      "#doctor-patients",
    );


  if (
    !patientList.length
  ) {
    root.innerHTML =
      `
      <div class="empty">

        <h3>
          Пациентов пока нет
        </h3>

        <p>
          Загрузите файл и проведите
          первый пакетный скрининг.
        </p>

      </div>
      `;

    return;
  }


  root.innerHTML =
    `
    <div class="table-wrap">

      <table>

        <thead>

          <tr>

            <th>
              Patient code
            </th>

            <th>
              Скринингов
            </th>

            <th>
              Последний
            </th>

            <th>
              Действие
            </th>

          </tr>

        </thead>


        <tbody>

          ${
            patientList
              .map(
                (
                  patient,
                  index,
                ) => `
                  <tr>

                    <td>

                      <strong>
                        ${
                          esc(
                            patient
                              .patient_code,
                          )
                        }
                      </strong>

                    </td>


                    <td>
                      ${
                        patient
                          .screening_count
                      }
                    </td>


                    <td>
                      ${
                        patient
                          .last_screening_at
                          ? date(
                              patient
                                .last_screening_at,
                            )
                          : "—"
                      }
                    </td>


                    <td>

                      <button
                        class="btn secondary small"
                        type="button"
                        data-patient="${index}"
                      >
                        Открыть →
                      </button>

                    </td>

                  </tr>
                `,
              )
              .join(
                "",
              )
          }

        </tbody>

      </table>

    </div>
    `;


  document
    .querySelectorAll(
      "[data-patient]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          () => {

            const patient =
              patientList[
                Number(
                  button.dataset
                    .patient,
                )
              ];


            if (
              patient
            ) {
              void openPatient(
                patient.patient_code,
              );
            }
          };
      },
    );
}


// ============================================================
// OPEN PATIENT
// ============================================================


async function openPatient(
  patientCode,
) {
  selectedPatient =
    patientCode;


  selectedHistory =
    null;


  selectedTrends =
    null;


  const root =
    document.querySelector(
      "#doctor-patient-detail",
    );


  root.innerHTML =
    `
    <section
      class="card"
      style="margin-top:40px"
    >

      <span class="eyebrow">
        Карточка пациента
      </span>

      <h2
        style="margin-top:14px"
      >
        Пациент
        ${
          esc(
            patientCode,
          )
        }
      </h2>

      <p role="status">

        <span class="loader"></span>

        Загружаем историю…

      </p>

    </section>
    `;


  // Сразу прокручиваем к карточке,
  // чтобы пользователь видел,
  // что его действие сработало.
  root.scrollIntoView({
    behavior:
      "smooth",

    block:
      "start",
  });


  try {
    selectedHistory =
      await getDoctorPatientHistory(
        patientCode,
      );


    renderPatientDetail();

  } catch (
    error
  ) {
    root.innerHTML =
      `
      <div
        class="error"
        style="margin-top:32px"
      >
        ${
          errorText(
            error,
          )
        }
      </div>
      `;
  }
}


// ============================================================
// PATIENT DETAIL
// ============================================================


function renderPatientDetail() {
  const root =
    document.querySelector(
      "#doctor-patient-detail",
    );


  const items =
    selectedHistory
      ?.items ||
    [];


  root.innerHTML =
    `
    <section
      style="margin-top:40px"
    >

      <div class="result-top">

        <div>

          <span class="eyebrow">
            Карточка пациента
          </span>

          <h2>
            ${
              esc(
                selectedPatient,
              )
            }
          </h2>

          <p class="subtitle">
            Скринингов:
            ${
              selectedHistory
                ?.total ??
              items.length
            }
          </p>

        </div>


        <div class="actions">

          <button
            class="btn secondary"
            type="button"
            id="doctor-show-trends"
          >
            Показать динамику
          </button>


          <button
            class="btn secondary"
            type="button"
            id="doctor-close-patient"
          >
            Закрыть карточку
          </button>

        </div>

      </div>


      ${
        items.length
          ? `
            <div class="table-wrap">

              <table>

                <thead>

                  <tr>

                    <th>
                      Дата
                    </th>

                    <th>
                      Итог
                    </th>

                    <th>
                      Полнота
                    </th>

                    <th>
                      Источник
                    </th>

                    <th>
                      Действия
                    </th>

                  </tr>

                </thead>


                <tbody>

                  ${
                    items
                      .map(
                        (
                          item,
                          index,
                        ) => `
                          <tr>

                            <td>
                              ${
                                date(
                                  item
                                    .created_at,
                                )
                              }
                            </td>


                            <td>

                              ${
                                esc(
                                  name(
                                    predictionText(
                                      item
                                        .prediction,
                                    ),
                                  ),
                                )
                              }

                            </td>


                            <td>
                              ${
                                coverageText(
                                  item
                                    .coverage,
                                )
                              }
                            </td>


                            <td>
                              ${
                                esc(
                                  item
                                    .source_type ||
                                  "—",
                                )
                              }
                            </td>


                            <td>

                              <div class="actions">

                                <button
                                  class="btn secondary small"
                                  type="button"
                                  data-open-screening="${index}"
                                >
                                  Результат
                                </button>


                                <button
                                  class="btn secondary small"
                                  type="button"
                                  data-doctor-pdf="${index}"
                                >
                                  PDF
                                </button>

                              </div>

                            </td>

                          </tr>
                        `,
                      )
                      .join(
                        "",
                      )
                  }

                </tbody>

              </table>

            </div>
          `
          : `
            <div class="empty">

              <h3>
                История пуста
              </h3>

              <p>
                У пациента пока нет
                сохранённых скринингов.
              </p>

            </div>
          `
      }


      <div
        id="doctor-trends"
        style="scroll-margin-top:24px"
      ></div>

    </section>
    `;


  bindPatientActions(
    items,
  );


  document
    .querySelector(
      "#doctor-close-patient",
    )
    ?.addEventListener(
      "click",
      () => {

        selectedPatient =
          null;


        selectedHistory =
          null;


        selectedTrends =
          null;


        root.innerHTML =
          "";


        document
          .querySelector(
            "#doctor-patients",
          )
          ?.scrollIntoView({
            behavior:
              "smooth",

            block:
              "start",
          });
      },
    );
}


// ============================================================
// PATIENT ACTIONS
// ============================================================


function bindPatientActions(
  items,
) {
  // ----------------------------------------------------------
  // OPEN RESULT
  // ----------------------------------------------------------


  document
    .querySelectorAll(
      "[data-open-screening]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          async () => {

            const item =
              items[
                Number(
                  button.dataset
                    .openScreening,
                )
              ];


            if (
              !item
            ) {
              return;
            }


            button.disabled =
              true;


            button.innerHTML =
              `
              <span class="loader"></span>
              Открываем…
              `;


            try {
              const result =
                await getDoctorPatientScreening(
                  selectedPatient,
                  item.screening_id,
                );


              state.result = {
                id:
                  item.screening_id,

                created_at:
                  item.created_at,

                labs:
                  [],

                result,
              };


              location.hash =
                "/result";

            } catch (
              error
            ) {
              toast(
                error?.message ||
                "Не удалось открыть результат.",
              );

            } finally {
              button.disabled =
                false;


              button.textContent =
                "Результат";
            }
          };
      },
    );


  // ----------------------------------------------------------
  // PDF
  // ----------------------------------------------------------


  document
    .querySelectorAll(
      "[data-doctor-pdf]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          async () => {

            const item =
              items[
                Number(
                  button.dataset
                    .doctorPdf,
                )
              ];


            if (
              !item
            ) {
              return;
            }


            button.disabled =
              true;


            button.innerHTML =
              `
              <span class="loader"></span>
              PDF…
              `;


            try {
              await downloadDoctorPatientPdf(
                selectedPatient,
                item.screening_id,
              );


              toast(
                "PDF скачан.",
              );

            } catch (
              error
            ) {
              toast(
                error?.message ||
                "Не удалось скачать PDF.",
              );

            } finally {
              button.disabled =
                false;


              button.textContent =
                "PDF";
            }
          };
      },
    );


  // ----------------------------------------------------------
  // TRENDS
  // ----------------------------------------------------------


  document
    .querySelector(
      "#doctor-show-trends",
    )
    ?.addEventListener(
      "click",
      loadPatientTrends,
    );
}


// ============================================================
// TRENDS
// ============================================================


async function loadPatientTrends() {
  const root =
    document.querySelector(
      "#doctor-trends",
    );


  root.innerHTML =
    `
    <div
      class="card"
      style="margin-top:32px"
    >

      <p role="status">

        <span class="loader"></span>

        Загружаем динамику…

      </p>

    </div>
    `;


  root.scrollIntoView({
    behavior:
      "smooth",

    block:
      "start",
  });


  try {
    selectedTrends =
      await getDoctorPatientTrends(
        selectedPatient,
      );


    renderPatientTrends();

  } catch (
    error
  ) {
    root.innerHTML =
      `
      <div
        class="error"
        style="margin-top:32px"
      >
        ${
          errorText(
            error,
          )
        }
      </div>
      `;
  }
}


// ============================================================
// TRENDS RENDER
// ============================================================


function renderPatientTrends() {
  const root =
    document.querySelector(
      "#doctor-trends",
    );


  const groups =
    selectedTrends
      ?.groups ||
    [];


  const available =
    groups.filter(
      (
        group,
      ) =>
        group.series
          ?.some(
            (
              series,
            ) =>
              series.points
                ?.length,
          ),
    );


  if (
    !available.length
  ) {
    root.innerHTML =
      `
      <div
        class="empty"
        style="margin-top:32px"
      >

        <h3>
          Динамики пока нет
        </h3>

        <p>
          Для пациента недостаточно
          сохранённых лабораторных данных.
        </p>

      </div>
      `;

    return;
  }


  root.innerHTML =
    `
    <section
      class="card"
      style="margin-top:32px"
    >

      <div class="result-top">

        <div>

          <span class="eyebrow">
            Динамика
          </span>

          <h3>
            Показатели пациента
          </h3>

        </div>

      </div>


      <p class="hint">
        Значения берутся из ранее
        сохранённых скринингов.
        Модель повторно не запускается.
      </p>


      ${
        available
          .map(
            (
              group,
            ) => `
              <div
                style="margin-top:28px"
              >

                <h3>
                  ${
                    esc(
                      group.label,
                    )
                  }
                </h3>


                ${
                  group.series
                    .filter(
                      (
                        series,
                      ) =>
                        series.points
                          ?.length,
                    )
                    .map(
                      (
                        series,
                      ) =>
                        renderMiniTrend(
                          series,
                        ),
                    )
                    .join(
                      "",
                    )
                }

              </div>
            `,
          )
          .join(
            "",
          )
      }

    </section>
    `;
}


// ============================================================
// MINI TREND
// ============================================================


function renderMiniTrend(
  series,
) {
  const points =
    [
      ...(
        series.points ||
        []
      ),
    ].sort(
      (
        a,
        b,
      ) =>
        new Date(
          a.date,
        ) -
        new Date(
          b.date,
        ),
    );


  if (
    !points.length
  ) {
    return "";
  }


  return `
    <div
      class="card"
      style="margin-top:16px"
    >

      <div class="result-top">

        <div>

          <strong>
            ${
              esc(
                series.label ||
                series.feature,
              )
            }
          </strong>

          ${
            series.unit
              ? `
                <span class="tag">
                  ${
                    esc(
                      series.unit,
                    )
                  }
                </span>
              `
              : ""
          }

        </div>

      </div>


      <div class="table-wrap">

        <table>

          <thead>

            <tr>

              <th>
                Дата
              </th>

              <th>
                Значение
              </th>

              <th>
                Референс
              </th>

            </tr>

          </thead>


          <tbody>

            ${
              points
                .map(
                  (
                    point,
                  ) => {

                    const low =
                      point.reference_low ??
                      series.reference_low;


                    const high =
                      point.reference_high ??
                      series.reference_high;


                    let reference =
                      "—";


                    if (
                      low !== null &&
                      low !== undefined &&
                      high !== null &&
                      high !== undefined
                    ) {
                      reference =
                        `${low}–${high}`;

                    } else if (
                      low !== null &&
                      low !== undefined
                    ) {
                      reference =
                        `≥ ${low}`;

                    } else if (
                      high !== null &&
                      high !== undefined
                    ) {
                      reference =
                        `≤ ${high}`;
                    }


                    return `
                      <tr>

                        <td>
                          ${
                            date(
                              point.date,
                            )
                          }
                        </td>


                        <td>

                          <strong>
                            ${
                              esc(
                                String(
                                  point.value,
                                ),
                              )
                            }
                          </strong>

                          ${
                            series.unit
                              ? ` ${esc(
                                  series.unit,
                                )}`
                              : ""
                          }

                        </td>


                        <td>
                          ${
                            esc(
                              reference,
                            )
                          }
                        </td>

                      </tr>
                    `;
                  },
                )
                .join(
                  "",
                )
            }

          </tbody>

        </table>

      </div>

    </div>
  `;
}
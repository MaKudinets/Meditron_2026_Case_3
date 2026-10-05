import {
  main,
  toast,
  errorText,
  page,
  back,
  esc,
} from "../components/index.js";

import {
  cfg,
} from "../api/client.js";

import {
  currentUser,
} from "../api/auth.js";

import {
  createScreening,
} from "../api/screening.js";

import {
  importPatientLabFile,
} from "../api/imports.js";

import {
  labs,
  groups,
  labCodes,
} from "../data/catalog.js";

import {
  state,
} from "../state.js";


// ============================================================
// PAGE
// ============================================================


export function screening() {
  // ----------------------------------------------------------
  // ROLE GUARD
  // ----------------------------------------------------------

  if (
    currentUser?.role ===
    "doctor"
  ) {
    location.hash =
      "/doctor";

    return;
  }


  main.innerHTML =
    page(
      `
      ${back()}

      <div class="result-top">

        <div>

          <h1>
            Новый скрининг
          </h1>

          <p class="subtitle">
            Введите показатели вручную
            или загрузите лабораторный файл
          </p>

        </div>


        <div class="actions">

          <input
            id="lab-file-input"
            type="file"
            accept=".csv,.xlsx,.pdf"
            hidden
          >


          <button
            class="btn secondary small"
            id="upload-lab-file"
            type="button"
          >
            ↑ Загрузить файл
          </button>


          <button
            class="btn secondary small"
            id="example"
            type="button"
          >
            Заполнить пример ↙
          </button>

        </div>

      </div>


      <div
        id="import-status"
        style="margin-bottom:24px"
      ></div>


      <div class="workspace">

        <form
          id="screening-form"
        >

          <section class="form-section">

            <h3>
              Данные пациента
            </h3>

            <p>
              Пол обязателен.
              Возраст можно не указывать.
            </p>


            <div class="fields">

              <div class="field">

                <label for="age_years">
                  Возраст, лет
                </label>

                <input
                  id="age_years"
                  name="age_years"
                  type="number"
                  min="0"
                  max="120"
                  step="1"
                  placeholder="Не указан"
                >

              </div>


              <div class="field">

                <label for="sex">
                  Пол *
                </label>

                <select
                  id="sex"
                  name="sex"
                  required
                >

                  <option
                    value=""
                    selected
                    disabled
                  >
                    Выберите
                  </option>

                  <option value="F">
                    Женский
                  </option>

                  <option value="M">
                    Мужской
                  </option>

                </select>

              </div>

            </div>

          </section>


          ${
            groups
              .map(
                (
                  group,
                ) => `
                  <section
                    class="form-section"
                    data-group="${esc(
                      group.key,
                    )}"
                  >

                    <h3>
                      ${
                        esc(
                          group.name,
                        )
                      }
                    </h3>

                    <p>
                      ${
                        esc(
                          group.description,
                        )
                      }
                    </p>


                    <div class="fields">

                      ${
                        group.codes
                          .map(
                            (
                              code,
                            ) => {

                              const lab =
                                labs[
                                  code
                                ];


                              return `
                                <div class="field">

                                  <label
                                    for="lab-${esc(
                                      code,
                                    )}"
                                  >
                                    ${
                                      esc(
                                        lab.label,
                                      )
                                    }

                                    ${
                                      lab.required
                                        ? " *"
                                        : ""
                                    }
                                  </label>


                                  <div class="input-wrap">

                                    <input
                                      id="lab-${esc(
                                        code,
                                      )}"
                                      name="${esc(
                                        code,
                                      )}"
                                      type="text"
                                      inputmode="decimal"
                                      autocomplete="off"
                                      placeholder="—"
                                      data-lab="${esc(
                                        code,
                                      )}"
                                      ${
                                        lab.required
                                          ? "required"
                                          : ""
                                      }
                                    >

                                    ${
                                      lab.unit
                                        ? `
                                          <span class="unit">
                                            ${
                                              esc(
                                                lab.unit,
                                              )
                                            }
                                          </span>
                                        `
                                        : ""
                                    }

                                  </div>

                                </div>
                              `;
                            },
                          )
                          .join(
                            "",
                          )
                      }

                    </div>

                  </section>
                `,
              )
              .join(
                "",
              )
          }


          <label class="check">

            <input
              type="checkbox"
              id="consent"
              required
            >

            <span>
              Я ознакомился с

              <a
                class="link"
                href="#/privacy"
              >
                условиями обработки данных
              </a>

              и понимаю, что результат
              скрининга не является диагнозом.
            </span>

          </label>


          <div
            id="form-error"
            role="alert"
          ></div>


          <div class="actions">

            <button
              class="btn"
              type="submit"
              id="submit-screening"
            >
              Провести скрининг →
            </button>


            <button
              type="reset"
              class="btn secondary"
            >
              Очистить форму
            </button>

          </div>

        </form>


        <aside class="side-card">

          <span class="eyebrow">
            Ваши данные
          </span>


          <h3
            style="margin-top:20px"
          >
            Заполнено

            <span id="filled">
              0
            </span>

            из
            ${
              labCodes.length
            }
          </h3>


          <div class="progress">

            <div
              id="fill-progress"
              style="width:0%"
            ></div>

          </div>


          <p>
            Обязательны пол
            и гемоглобин.
          </p>


          <p>
            После загрузки файла
            обязательно проверьте
            автоматически распознанные данные.
          </p>


          <img
            src="assets/robot-about.webp"
            alt="Робот Meditron"
            loading="lazy"
          >


          <p class="hint">
            ${
              cfg.mode ===
              "demo"
                ? "Используется демонстрационный режим."
                : "Модель запускается только после нажатия кнопки скрининга."
            }
          </p>

        </aside>

      </div>
      `,
    );


  const form =
    document.querySelector(
      "#screening-form",
    );


  const fileInput =
    document.querySelector(
      "#lab-file-input",
    );


  const uploadButton =
    document.querySelector(
      "#upload-lab-file",
    );


  const importStatus =
    document.querySelector(
      "#import-status",
    );


  let importedMetadata =
    {};


  let importedFilename =
    null;


  // ==========================================================
  // DRAFT
  // ==========================================================


  function saveDraft() {
    state.formDraft =
      Object.fromEntries(
        new FormData(
          form,
        ),
      );


    state.formDraft.consent =
      form.querySelector(
        "#consent",
      ).checked;


    state.formDraft
      ._importedMetadata =
        importedMetadata;


    state.formDraft
      ._importedFilename =
        importedFilename;
  }


  // ==========================================================
  // COUNTER
  // ==========================================================


  function update() {
    const filled =
      [
        ...form.querySelectorAll(
          "[data-lab]",
        ),
      ].filter(
        (
          input,
        ) =>
          input.value.trim(),
      ).length;


    document
      .querySelector(
        "#filled",
      )
      .textContent =
        filled;


    document
      .querySelector(
        "#fill-progress",
      )
      .style.width =
        `${
          (
            filled /
            labCodes.length
          ) *
          100
        }%`;


    saveDraft();
  }


  // ==========================================================
  // RESTORE DRAFT
  // ==========================================================


  if (
    state.formDraft
  ) {
    importedMetadata =
      state.formDraft
        ._importedMetadata ||
      {};


    importedFilename =
      state.formDraft
        ._importedFilename ||
      null;


    for (
      const [
        key,
        value,
      ]
      of Object.entries(
        state.formDraft,
      )
    ) {
      if (
        key ===
          "consent" ||
        key.startsWith(
          "_",
        )
      ) {
        continue;
      }


      const input =
        form.elements
          .namedItem(
            key,
          );


      if (
        input
      ) {
        input.value =
          value;
      }
    }


    form
      .querySelector(
        "#consent",
      )
      .checked =
        !!state
          .formDraft
          .consent;
  }


  form.addEventListener(
    "input",
    update,
  );


  form.addEventListener(
    "change",
    update,
  );


  // ==========================================================
  // IMPORT SUMMARY
  // ==========================================================


  function renderImportSummary(
    imported,
    appliedCount,
  ) {
    const warnings =
      imported.warnings ||
      [];


    const unrecognized =
      imported.unrecognized ||
      [];


    importStatus.innerHTML =
      `
      <section class="card">

        <span class="eyebrow">
          Файл разобран
        </span>


        <h3
          style="margin-top:14px"
        >
          ${
            esc(
              imported.filename ||
              "Лабораторный файл",
            )
          }
        </h3>


        <p>
          Распознано сервером:
          <strong>
            ${
              imported.recognized_count ??
              0
            }
          </strong>
        </p>


        <p>
          Подставлено в форму:
          <strong>
            ${
              appliedCount
            }
          </strong>
        </p>


        ${
          warnings.length
            ? `
              <div
                style="margin-top:18px"
              >

                <strong>
                  Предупреждения:
                </strong>

                <ul>

                  ${
                    warnings
                      .map(
                        (
                          item,
                        ) => `
                          <li>
                            ${
                              esc(
                                item,
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
            `
            : ""
        }


        ${
          unrecognized.length
            ? `
              <details
                style="margin-top:18px"
              >

                <summary>
                  Не распознано:
                  ${
                    unrecognized.length
                  }
                </summary>

                <ul>

                  ${
                    unrecognized
                      .map(
                        (
                          item,
                        ) => `
                          <li>
                            ${
                              esc(
                                item.name ??
                                "Неизвестный показатель",
                              )
                            }

                            ${
                              item.value !==
                              undefined
                                ? `: ${esc(
                                    String(
                                      item.value,
                                    ),
                                  )}`
                                : ""
                            }
                          </li>
                        `,
                      )
                      .join(
                        "",
                      )
                  }

                </ul>

              </details>
            `
            : ""
        }


        <p
          class="hint"
          style="margin-top:18px"
        >
          Значения только подставлены
          в форму. Проверьте их
          перед запуском скрининга.
        </p>

      </section>
      `;
  }


  // ==========================================================
  // APPLY IMPORT
  // ==========================================================


  function applyImportedData(
    imported,
  ) {
    const features =
      imported.features ||
      {};


    importedMetadata =
      imported.metadata ||
      {};


    importedFilename =
      imported.filename ||
      null;


    let appliedCount =
      0;


    for (
      const [
        key,
        value,
      ]
      of Object.entries(
        features,
      )
    ) {
      const input =
        form.elements
          .namedItem(
            key,
          );


      if (
        !input ||
        value === null ||
        value === undefined
      ) {
        continue;
      }


      input.value =
        String(
          value,
        );


      appliedCount +=
        1;
    }


    update();


    renderImportSummary(
      imported,
      appliedCount,
    );
  }


  // ==========================================================
  // FILE
  // ==========================================================


  uploadButton.onclick =
    () => {
      fileInput.click();
    };


  fileInput.addEventListener(
    "change",
    async () => {

      const file =
        fileInput
          .files?.[0];


      if (
        !file
      ) {
        return;
      }


      uploadButton.disabled =
        true;


      uploadButton.innerHTML =
        `
        <span class="loader"></span>
        Разбираем файл…
        `;


      importStatus.innerHTML =
        "";


      try {
        const imported =
          await importPatientLabFile(
            file,
          );


        applyImportedData(
          imported,
        );


        toast(
          "Файл разобран. Проверьте подставленные данные.",
        );

      } catch (
        error
      ) {
        importStatus.innerHTML =
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
        uploadButton.disabled =
          false;


        uploadButton.textContent =
          "↑ Загрузить файл";


        fileInput.value =
          "";
      }
    },
  );


  // ==========================================================
  // RESET
  // ==========================================================


  form.addEventListener(
    "reset",
    () => {

      importedMetadata =
        {};


      importedFilename =
        null;


      state.formDraft =
        null;


      importStatus.innerHTML =
        "";


      document
        .querySelector(
          "#form-error",
        )
        .innerHTML =
          "";


      setTimeout(
        () => {

          document
            .querySelector(
              "#filled",
            )
            .textContent =
              "0";


          document
            .querySelector(
              "#fill-progress",
            )
            .style.width =
              "0%";

        },
        0,
      );
    },
  );


  // ==========================================================
  // EXAMPLE
  // ==========================================================


  document
    .querySelector(
      "#example",
    )
    .onclick =
      () => {

        importedMetadata =
          {};


        importedFilename =
          null;


        importStatus.innerHTML =
          "";


        const values = {
          age_years:
            22,

          sex:
            "F",

          hemoglobin:
            132,

          RBC:
            4.5,

          hematocrit:
            41,

          MCV:
            91,

          MCH:
            30,

          MCHC:
            322,

          RDW:
            13,

          platelets:
            250,

          WBC:
            6.2,

          ferritin:
            16,

          serum_iron:
            11,

          transferrin:
            3.2,

          TIBC:
            72,

          TSAT:
            16,

          vitamin_B12:
            350,

          folate:
            8,

          CRP:
            1.2,

          creatinine:
            72,

          eGFR:
            100,

          TSH:
            1.8,

          albumin:
            45,
        };


        for (
          const [
            key,
            value,
          ]
          of Object.entries(
            values,
          )
        ) {
          const input =
            form.elements
              .namedItem(
                key,
              );


          if (
            input
          ) {
            input.value =
              value;
          }
        }


        update();


        toast(
          "Пример заполнен.",
        );
      };


  // ==========================================================
  // SUBMIT
  // ==========================================================


  form.onsubmit =
    async (
      event,
    ) => {

      event.preventDefault();


      if (
        state.busy
      ) {
        return;
      }


      const version =
        state.routeVersion;


      const errorBox =
        document.querySelector(
          "#form-error",
        );


      errorBox.innerHTML =
        "";


      const button =
        document.querySelector(
          "#submit-screening",
        );


      try {
        const ageRaw =
          form.elements
            .namedItem(
              "age_years",
            )
            .value
            .trim();


        const age_years =
          ageRaw ===
            ""
            ? null
            : Number(
                ageRaw,
              );


        if (
          age_years !==
            null &&
          (
            !Number.isFinite(
              age_years,
            ) ||
            age_years < 0 ||
            age_years > 120
          )
        ) {
          throw new Error(
            "Возраст должен быть числом от 0 до 120.",
          );
        }


        const sex =
          form.elements
            .namedItem(
              "sex",
            )
            .value;


        if (
          sex !==
            "F" &&
          sex !==
            "M"
        ) {
          throw new Error(
            "Укажите пол пациента.",
          );
        }


        const labValues =
          labCodes.map(
            (
              code,
            ) => {

              const raw =
                form.elements
                  .namedItem(
                    code,
                  )
                  .value
                  .trim();


              const value =
                raw ===
                  ""
                  ? null
                  : Number(
                      raw.replace(
                        ",",
                        ".",
                      ),
                    );


              if (
                raw &&
                (
                  !Number.isFinite(
                    value,
                  ) ||
                  value < 0
                )
              ) {
                throw new Error(
                  `Проверьте показатель «${
                    labs[
                      code
                    ].label
                  }».`,
                );
              }


              return {
                code,

                value,

                unit:
                  labs[
                    code
                  ].unit ||
                  null,
              };
            },
          );


        const data = {
          age_years,

          sex,

          labs:
            labValues,

          lab_metadata:
            importedMetadata,

          source_filename:
            importedFilename,
        };


        state.busy =
          true;


        button.disabled =
          true;


        button.innerHTML =
          `
          <span class="loader"></span>
          Анализируем…
          `;


        state.result =
          await createScreening(
            data,
          );


        state.formDraft =
          null;


        importedMetadata =
          {};


        importedFilename =
          null;


        if (
          version ===
          state.routeVersion
        ) {
          location.hash =
            "/result";
        }

      } catch (
        error
      ) {
        if (
          version ===
          state.routeVersion
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
        }

      } finally {
        state.busy =
          false;


        if (
          version ===
          state.routeVersion
        ) {
          button.disabled =
            false;


          button.textContent =
            "Провести скрининг →";
        }
      }
    };


  update();
}
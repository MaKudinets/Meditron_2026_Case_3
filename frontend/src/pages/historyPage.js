import {
  main,
  esc,
  pct,
  date,
  name,
  errorText,
  demoNotice,
  page,
  back,
  tabs,
  gated,
  toast,
} from "../components/index.js";

import {
  cfg,
} from "../api/client.js";

import {
  currentUser,
} from "../api/auth.js";

import {
  getHistory,
  getScreening,
  deleteScreening,
  downloadScreeningPdf,
} from "../api/history.js";

import {
  clearHistory,
} from "../mocks/screening.js";

import {
  state,
} from "../state.js";


// ============================================================
// HELPERS
// ============================================================


function sourceLabel(
  sourceType,
) {
  if (
    sourceType === "file"
  ) {
    return "Файл";
  }


  if (
    sourceType === "manual"
  ) {
    return "Вручную";
  }


  return (
    sourceType ||
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
// HISTORY PAGE
// ============================================================


export async function historyPage() {
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


  // ----------------------------------------------------------
  // AUTH GUARD
  // ----------------------------------------------------------

  if (
    gated()
  ) {
    return;
  }


  const version =
    state.routeVersion;


  main.innerHTML =
    page(
      `
      ${back()}

      <h1>
        История анализов
      </h1>

      <p class="subtitle">
        Загружаем предыдущие скрининги…
      </p>

      ${tabs(
        "history",
      )}

      <p role="status">
        <span class="loader"></span>
        Загружаем историю…
      </p>
      `,
    );


  try {
    state.cachedHistory =
      await getHistory();


    if (
      version !==
      state.routeVersion
    ) {
      return;
    }


    renderHistory(
      state.cachedHistory,
    );

  } catch (
    error
  ) {
    if (
      version !==
      state.routeVersion
    ) {
      return;
    }


    main.innerHTML =
      page(
        `
        ${back()}

        <h1>
          История анализов
        </h1>

        ${tabs(
          "history",
        )}

        <div
          class="error"
          role="alert"
        >
          ${
            errorText(
              error,
            )
          }
        </div>

        <button
          class="btn secondary"
          id="retry-history"
          type="button"
        >
          Повторить
        </button>
        `,
      );


    document
      .querySelector(
        "#retry-history",
      )
      ?.addEventListener(
        "click",
        historyPage,
      );
  }
}


// ============================================================
// RENDER
// ============================================================


function renderHistory(
  items,
) {
  main.innerHTML =
    page(
      `
      ${back()}

      <div class="result-top">

        <div>

          <h1>
            История анализов
          </h1>

          <p class="subtitle">
            ${
              items.length
            }
            ${
              items.length === 1
                ? "обследование"
                : "обследований"
            }
          </p>

        </div>


        <a
          class="btn"
          href="#/screening"
        >
          + Новый скрининг
        </a>

      </div>


      ${tabs(
        "history",
      )}


      ${demoNotice()}


      ${
        items.length
          ? renderTable(
              items,
            )
          : `
            <div class="empty">

              <h3>
                Пока нет обследований
              </h3>

              <p>
                После первого
                сохранённого скрининга
                здесь появится история.
              </p>

              <a
                class="btn"
                href="#/screening"
              >
                Начать →
              </a>

            </div>
          `
      }


      ${
        cfg.mode ===
          "demo" &&
        items.length
          ? `
            <div class="actions">

              <button
                id="clear-history"
                class="btn secondary small"
                type="button"
              >
                Очистить демонстрационную историю
              </button>

            </div>
          `
          : ""
      }
      `,
    );


  bindHistoryActions(
    items,
  );


  document
    .querySelector(
      "#clear-history",
    )
    ?.addEventListener(
      "click",
      () => {

        clearHistory();

        historyPage();
      },
    );
}


// ============================================================
// TABLE
// ============================================================


function renderTable(
  items,
) {
  return `
    <div class="table-wrap">

      <table>

        <thead>

          <tr>

            <th>
              Дата
            </th>

            <th>
              Результат
            </th>

            <th>
              Полнота данных
            </th>

            <th>
              Источник
            </th>

            <th>
              Версия
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
                ) => {

                  const prediction =
                    item.prediction ||
                    {};


                  return `
                    <tr>

                      <td>
                        ${
                          date(
                            item.created_at,
                          )
                        }
                      </td>


                      <td>

                        <strong>
                          ${
                            esc(
                              name(
                                prediction
                                  .anemia_class ||
                                "",
                              ),
                            )
                          }
                        </strong>


                        ${
                          prediction
                            .deficiency_cause
                            ? `
                              <div class="hint">
                                ${
                                  esc(
                                    name(
                                      prediction
                                        .deficiency_cause,
                                    ),
                                  )
                                }
                              </div>
                            `
                            : ""
                        }

                      </td>


                      <td>
                        ${
                          coverageText(
                            item.coverage,
                          )
                        }
                      </td>


                      <td>
                        ${
                          esc(
                            sourceLabel(
                              item.source_type,
                            ),
                          )
                        }
                      </td>


                      <td>
                        ${
                          esc(
                            item.bundle_version ||
                            "—",
                          )
                        }
                      </td>


                      <td>

                        <div class="actions">

                          <button
                            class="btn secondary small"
                            type="button"
                            data-open="${index}"
                          >
                            Открыть
                          </button>


                          ${
                            cfg.mode !==
                            "demo"
                              ? `
                                <button
                                  class="btn secondary small"
                                  type="button"
                                  data-pdf="${index}"
                                >
                                  PDF
                                </button>


                                <button
                                  class="btn secondary small"
                                  type="button"
                                  data-delete="${index}"
                                >
                                  Удалить
                                </button>
                              `
                              : ""
                          }

                        </div>

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
  `;
}


// ============================================================
// EVENTS
// ============================================================


function bindHistoryActions(
  items,
) {
  // ----------------------------------------------------------
  // OPEN
  // ----------------------------------------------------------

  document
    .querySelectorAll(
      "[data-open]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          async () => {

            const index =
              Number(
                button.dataset.open,
              );


            const item =
              items[
                index
              ];


            if (
              !item
            ) {
              return;
            }


            const version =
              state.routeVersion;


            button.disabled =
              true;


            button.innerHTML =
              `
              <span class="loader"></span>
              Открываем…
              `;


            try {
              const fullResult =
                await getScreening(
                  item.screening_id,
                );


              if (
                version !==
                state.routeVersion
              ) {
                return;
              }


              state.result = {
                id:
                  item.screening_id,

                created_at:
                  item.created_at,

                labs:
                  [],

                result:
                  fullResult,
              };


              location.hash =
                "/result";

            } catch (
              error
            ) {
              if (
                version ===
                state.routeVersion
              ) {
                toast(
                  error?.message ||
                  "Не удалось открыть скрининг.",
                );
              }

            } finally {
              button.disabled =
                false;


              button.textContent =
                "Открыть";
            }
          };
      },
    );


  // ----------------------------------------------------------
  // PDF
  // ----------------------------------------------------------

  document
    .querySelectorAll(
      "[data-pdf]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          async () => {

            const index =
              Number(
                button.dataset.pdf,
              );


            const item =
              items[
                index
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
              await downloadScreeningPdf(
                item.screening_id,
              );


              toast(
                "PDF-отчёт скачан.",
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
  // DELETE
  // ----------------------------------------------------------

  document
    .querySelectorAll(
      "[data-delete]",
    )
    .forEach(
      (
        button,
      ) => {

        button.onclick =
          async () => {

            const index =
              Number(
                button.dataset.delete,
              );


            const item =
              items[
                index
              ];


            if (
              !item
            ) {
              return;
            }


            const confirmed =
              window.confirm(
                "Удалить этот скрининг из истории?",
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
              Удаляем…
              `;


            try {
              await deleteScreening(
                item.screening_id,
              );


              toast(
                "Скрининг удалён.",
              );


              await historyPage();

            } catch (
              error
            ) {
              toast(
                error?.message ||
                "Не удалось удалить скрининг.",
              );


              button.disabled =
                false;


              button.textContent =
                "Удалить";
            }
          };
      },
    );
}
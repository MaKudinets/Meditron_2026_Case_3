import {
  main,
  esc,
  pct,
  date,
  name,
  medicalNotice,
  demoNotice,
  page,
  labTable,
  download,
} from "../components/index.js";

import {
  cfg,
} from "../api/client.js";

import {
  labs,
  conditions,
} from "../data/catalog.js";

import {
  state,
} from "../state.js";


// ============================================================
// LABELS
// ============================================================


const confidenceLabels = {
  high:
    "Высокая",

  moderate:
    "Умеренная",

  low:
    "Низкая",
};


const ruleStateLabels = {
  supports:
    "Поддерживает вывод",

  against:
    "Противоречит выводу",

  unknown:
    "Недостаточно данных",
};


const directionLabels = {
  supports:
    "Поддерживает",

  against:
    "Против",

  unknown:
    "Неопределённо",
};


// ============================================================
// HELPERS
// ============================================================


function featureLabel(
  feature,
) {
  return (
    labs[
      feature
    ]?.label ||
    feature
  );
}


function targetLabel(
  target,
) {
  return (
    conditions[
      target
    ] ||
    name(
      target,
    )
  );
}


function formatValue(
  value,
) {
  if (
    value ===
      null ||
    value ===
      undefined ||
    value ===
      ""
  ) {
    return "—";
  }

  if (
    typeof value ===
    "number"
  ) {
    return value
      .toLocaleString(
        "ru-RU",
        {
          maximumFractionDigits:
            4,
        },
      );
  }

  return String(
    value,
  );
}


function formatBoolean(
  value,
) {
  return value
    ? "Да"
    : "Нет";
}


function clampPercent(
  value,
) {
  const numeric =
    Number(
      value,
    );

  if (
    !Number.isFinite(
      numeric,
    )
  ) {
    return 0;
  }

  return Math.max(
    0,
    Math.min(
      100,
      numeric *
        100,
    ),
  );
}


// ============================================================
// PREDICTION SUMMARY
// ============================================================


function renderPrediction(
  result,
) {
  const prediction =
    result.prediction;


  return `
    <section class="card">

      <span class="eyebrow">
        Итог скрининга
      </span>

      <h2
        style="
          margin-top:16px;
          margin-bottom:20px
        "
      >
        ${
          esc(
            name(
              prediction
                .anemia_class,
            ),
          )
        }
      </h2>


      <div class="result-grid">

        <article class="result-card">

          <span class="tag">
            Анемия
          </span>

          <h3
            style="margin-top:20px"
          >
            ${
              prediction
                .anemia
                ? "Признаки выявлены"
                : "Признаки не выявлены"
            }
          </h3>

          <p>
            ${
              formatBoolean(
                prediction
                  .anemia,
              )
            }
          </p>

        </article>


        <article class="result-card">

          <span class="tag">
            Предполагаемая причина
          </span>

          <h3
            style="margin-top:20px"
          >
            ${
              esc(
                name(
                  prediction
                    .deficiency_cause,
                ),
              )
            }
          </h3>

        </article>

      </div>

    </section>
  `;
}


// ============================================================
// CONFIDENCE
// ============================================================


function renderConfidence(
  result,
) {
  const confidence =
    result.confidence;


  return `
    <section class="card">

      <h3>
        Уверенность результата
      </h3>


      <div class="percent">
        ${
          pct(
            confidence
              .certainty,
          )
        }
      </div>


      <div class="bar">

        <div
          style="
            width:${
              clampPercent(
                confidence
                  .certainty,
              )
            }%
          "
        ></div>

      </div>


      <div class="scale">

        <span>
          0%
        </span>

        <span>
          ${
            esc(
              confidenceLabels[
                confidence
                  .level
              ] ||
              confidence
                .level,
            )
          }
        </span>

        <span>
          100%
        </span>

      </div>


      ${
        confidence
          .basis
          ? `
            <p
              style="margin-top:18px"
            >
              ${
                esc(
                  confidence
                    .basis,
                )
              }
            </p>
          `
          : ""
      }


      ${
        confidence
          .limiting_target
          ? `
            <p class="hint">

              Ограничивающее состояние:

              <strong>
                ${
                  esc(
                    targetLabel(
                      confidence
                        .limiting_target,
                    ),
                  )
                }
              </strong>

            </p>
          `
          : ""
      }

    </section>
  `;
}


// ============================================================
// DEFICIENCIES
// ============================================================


function renderDeficiencies(
  result,
) {
  const entries =
    Object.entries(
      result.deficiencies ||
        {},
    );


  if (
    !entries.length
  ) {
    return `
      <section class="card">
        <h3>
          Проверенные состояния
        </h3>

        <p>
          Сервер не вернул
          результаты отдельных состояний.
        </p>
      </section>
    `;
  }


  const cards =
    entries
      .sort(
        (
          a,
          b,
        ) =>
          Number(
            b[1]
              .probability,
          ) -
          Number(
            a[1]
              .probability,
          ),
      )
      .map(
        (
          [
            target,
            item,
          ],
        ) => {

          const probability =
            Number(
              item.probability,
            );

          return `
            <article class="result-card">

              <span class="tag">
                ${
                  item
                    .prediction
                    ? "Скрининговый признак выявлен"
                    : "Не выявлен"
                }
              </span>


              <h3
                style="margin-top:20px"
              >
                ${
                  esc(
                    targetLabel(
                      target,
                    ),
                  )
                }
              </h3>


              <div class="percent">

                ${
                  pct(
                    probability,
                  )
                }

              </div>


              <div class="bar">

                <div
                  style="
                    width:${
                      clampPercent(
                        probability,
                      )
                    }%
                  "
                ></div>

              </div>


              <div class="scale">

                <span>
                  0%
                </span>

                <span>
                  Вероятность
                </span>

                <span>
                  100%
                </span>

              </div>


              <div
                style="
                  margin-top:20px
                "
              >

                <p>

                  Порог модели:

                  <strong>
                    ${
                      pct(
                        item
                          .threshold,
                      )
                    }
                  </strong>

                </p>


                ${
                  item
                    .rule_score !==
                    null &&
                  item
                    .rule_score !==
                    undefined
                    ? `
                      <p>

                        Оценка экспертных правил:

                        <strong>
                          ${
                            pct(
                              item
                                .rule_score,
                            )
                          }
                        </strong>

                      </p>
                    `
                    : ""
                }


                ${
                  item
                    .rule_state
                    ? `
                      <p class="hint">

                        Экспертный слой:

                        ${
                          esc(
                            ruleStateLabels[
                              item
                                .rule_state
                            ] ||
                            item
                              .rule_state,
                          )
                        }

                      </p>
                    `
                    : ""
                }

              </div>

            </article>
          `;
        },
      )
      .join(
        "",
      );


  return `
    <section
      style="margin-top:32px"
    >

      <h2>
        Проверенные состояния
      </h2>

      <p class="subtitle">
        Вероятности отдельных веток
        скрининговой модели
      </p>

      <div class="result-grid">

        ${cards}

      </div>

    </section>
  `;
}


// ============================================================
// DATA QUALITY
// ============================================================


function renderDataQuality(
  result,
) {
  const quality =
    result.data_quality;


  const warnings =
    quality.warnings ||
    [];


  return `
    <section class="card">

      <h3>
        Качество и полнота данных
      </h3>


      <div class="percent">

        ${
          pct(
            quality.coverage,
          )
        }

      </div>


      <div class="bar">

        <div
          style="
            width:${
              clampPercent(
                quality
                  .coverage,
              )
            }%
          "
        ></div>

      </div>


      <p
        class="hint"
        style="margin-top:18px"
      >
        Полнота входных данных,
        использованных системой.
      </p>


      ${
        quality
          .used_features
          ?.length
          ? `
            <p>
              Использовано показателей:
              <strong>
                ${
                  quality
                    .used_features
                    .length
                }
              </strong>
            </p>
          `
          : ""
      }


      ${
        quality
          .missing_features
          ?.length
          ? `
            <details
              style="margin-top:16px"
            >

              <summary>
                Не передано показателей:
                ${
                  quality
                    .missing_features
                    .length
                }
              </summary>

              <ul>

                ${
                  quality
                    .missing_features
                    .map(
                      (
                        feature,
                      ) => `
                        <li>
                          ${
                            esc(
                              featureLabel(
                                feature,
                              ),
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

            </details>
          `
          : ""
      }


      ${
        warnings.length
          ? `
            <div
              style="margin-top:20px"
            >

              <strong>
                Предупреждения:
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
          `
          : `
            <p
              style="margin-top:18px"
            >
              Сервер не сообщил
              дополнительных предупреждений
              о качестве данных.
            </p>
          `
      }

    </section>
  `;
}


// ============================================================
// EVIDENCE
// ============================================================


function renderEvidence(
  result,
) {
  const evidence =
    result.evidence ||
    [];


  if (
    !evidence.length
  ) {
    return "";
  }


  return `
    <section
      class="card"
      style="margin-top:32px"
    >

      <h3>
        Признаки, учтённые экспертным слоем
      </h3>


      <div
        style="overflow-x:auto"
      >

        <table>

          <thead>

            <tr>
              <th>
                Состояние
              </th>

              <th>
                Показатель
              </th>

              <th>
                Значение
              </th>

              <th>
                Критерий
              </th>

              <th>
                Направление
              </th>

              <th>
                Сила
              </th>
            </tr>

          </thead>


          <tbody>

            ${
              evidence
                .map(
                  (
                    item,
                  ) => `
                    <tr>

                      <td>
                        ${
                          esc(
                            targetLabel(
                              item
                                .target,
                            ),
                          )
                        }
                      </td>

                      <td>
                        ${
                          esc(
                            featureLabel(
                              item
                                .feature,
                            ),
                          )
                        }
                      </td>

                      <td>
                        ${
                          esc(
                            formatValue(
                              item
                                .value,
                            ),
                          )
                        }
                      </td>

                      <td>
                        ${
                          esc(
                            item
                              .criterion,
                          )
                        }
                      </td>

                      <td>
                        ${
                          esc(
                            directionLabels[
                              item
                                .direction
                            ] ||
                            item
                              .direction,
                          )
                        }
                      </td>

                      <td>
                        ${
                          esc(
                            item
                              .strength,
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
// CONFLICTS
// ============================================================


function renderConflicts(
  result,
) {
  const conflicts =
    result.conflicts ||
    [];


  if (
    !conflicts.length
  ) {
    return "";
  }


  return `
    <section
      class="card"
      style="margin-top:32px"
    >

      <h3>
        Расхождения между моделью
        и экспертными правилами
      </h3>


      <p class="hint">
        Этот раздел показывает случаи,
        когда ML-компонент и логический
        экспертный слой дают
        различающиеся сигналы.
      </p>


      ${
        conflicts
          .map(
            (
              conflict,
            ) => `
              <div
                class="notice"
                style="margin-top:16px"
              >

                <div>

                  <strong>
                    ${
                      esc(
                        targetLabel(
                          conflict
                            .target,
                        ),
                      )
                    }
                  </strong>

                  <p
                    style="
                      margin-top:8px
                    "
                  >
                    ${
                      esc(
                        conflict
                          .message,
                      )
                    }
                  </p>

                  <p class="hint">

                    Вероятность модели:
                    ${
                      pct(
                        conflict
                          .ensemble_probability,
                      )
                    }

                    ·

                    Rule score:
                    ${
                      pct(
                        conflict
                          .rule_score,
                      )
                    }

                  </p>

                </div>

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
// RECOMMENDED TESTS
// ============================================================


function renderRecommendedTests(
  result,
) {
  const items =
    result
      .recommended_next_tests ||
    [];


  if (
    !items.length
  ) {
    return "";
  }


  return `
    <section
      class="card"
      style="margin-top:32px"
    >

      <h3>
        Какие данные могут уточнить результат
      </h3>


      <p class="hint">
        Это рекомендации по дополнительным
        лабораторным данным для уточнения
        скрининга, а не назначение лечения.
      </p>


      <table>

        <thead>

          <tr>

            <th>
              Исследование
            </th>

            <th>
              Связано с
            </th>

            <th>
              Причина
            </th>

          </tr>

        </thead>


        <tbody>

          ${
            items
              .map(
                (
                  item,
                ) => `
                  <tr>

                    <td>
                      ${
                        esc(
                          item
                            .test,
                        )
                      }
                    </td>

                    <td>
                      ${
                        esc(
                          targetLabel(
                            item
                              .target,
                          ),
                        )
                      }
                    </td>

                    <td>
                      ${
                        esc(
                          item
                            .reason,
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

    </section>
  `;
}


// ============================================================
// MODEL
// ============================================================


function renderModelInfo(
  result,
) {
  const model =
    result.model ||
    {};


  if (
    !model.bundle_name &&
    !model.bundle_version
  ) {
    return "";
  }


  return `
    <section
      class="card"
      style="margin-top:32px"
    >

      <h3>
        Версия системы
      </h3>


      ${
        model
          .bundle_name
          ? `
            <p>
              Bundle:
              <strong>
                ${
                  esc(
                    model
                      .bundle_name,
                  )
                }
              </strong>
            </p>
          `
          : ""
      }


      ${
        model
          .bundle_version
          ? `
            <p>
              Версия:
              <strong>
                ${
                  esc(
                    model
                      .bundle_version,
                  )
                }
              </strong>
            </p>
          `
          : ""
      }

    </section>
  `;
}


// ============================================================
// MAIN PAGE
// ============================================================


export function results() {
  if (
    !state.result
  ) {
    main.innerHTML =
      page(
        `
        <div class="empty">

          <h1>
            Результат ещё не получен
          </h1>

          <p>
            Начните новый скрининг
            или откройте анализ
            из истории.
          </p>

          <a
            class="btn"
            href="#/screening"
          >
            Новый скрининг →
          </a>

        </div>
        `,
      );

    return;
  }


  const result =
    state.result.result;


  if (
    !result
  ) {
    main.innerHTML =
      page(
        `
        <div class="empty">

          <h1>
            Результат недоступен
          </h1>

          <p>
            Ответ сервера отсутствует
            или имеет неверный формат.
          </p>

          <a
            class="btn"
            href="#/screening"
          >
            Новый скрининг →
          </a>

        </div>
        `,
      );

    return;
  }


  main.innerHTML =
    page(
      `
      <a
        class="back"
        href="#/screening"
      >
        ← К форме анализов
      </a>


      <div class="result-top">

        <div>

          <h1>
            Результат скрининга
          </h1>

          <p class="subtitle">

            ${
              date(
                state
                  .result
                  .created_at,
              )
            }

            ·

            ${
              cfg.mode ===
                "demo"
                ? "Демонстрационный ответ"
                : "Ответ Meditron API"
            }

            ${
              result
                .model
                ?.bundle_version
                ? `
                  · версия
                  ${
                    esc(
                      result
                        .model
                        .bundle_version,
                    )
                  }
                `
                : ""
            }

          </p>

        </div>


        <button
          class="btn secondary"
          id="print-result"
          type="button"
        >
          ↓ Печать / PDF
        </button>

      </div>


      ${demoNotice()}


      ${renderPrediction(
        result,
      )}


      <div
        class="split"
        style="margin-top:32px"
      >

        ${
          renderConfidence(
            result,
          )
        }

        ${
          renderDataQuality(
            result,
          )
        }

      </div>


      ${
        renderDeficiencies(
          result,
        )
      }


      ${
        renderEvidence(
          result,
        )
      }


      ${
        renderConflicts(
          result,
        )
      }


      ${
        renderRecommendedTests(
          result,
        )
      }


      <section
        style="margin-top:32px"
      >

        <h3>
          Переданные показатели
        </h3>

        ${
          labTable(
            state
              .result
              .labs ||
              [],
          )
        }

      </section>


      ${
        renderModelInfo(
          result,
        )
      }


      ${
        result
          .disclaimer
          ? `
            <section
              class="card"
              style="margin-top:32px"
            >

              <h3>
                Важно
              </h3>

              <p>
                ${
                  esc(
                    result
                      .disclaimer,
                  )
                }
              </p>

            </section>
          `
          : medicalNotice()
      }


      <div class="actions">

        <a
          href="#/history"
          class="btn"
        >
          История анализов →
        </a>


        <button
          class="btn secondary"
          id="download-result"
          type="button"
        >
          ↓ Скачать JSON
        </button>


        <a
          class="btn secondary"
          href="#/screening"
        >
          Новый скрининг
        </a>

      </div>
      `,
    );


  // ==========================================================
  // PRINT
  // ==========================================================


  document
    .querySelector(
      "#print-result",
    )
    .onclick =
      () =>
        window.print();


  // ==========================================================
  // JSON EXPORT
  // ==========================================================


  document
    .querySelector(
      "#download-result",
    )
    .onclick =
      () =>
        download(
          `meditron-${
            result
              .screening_id
          }.json`,

          JSON.stringify(
            result,
            null,
            2,
          ),

          "application/json",
        );
}
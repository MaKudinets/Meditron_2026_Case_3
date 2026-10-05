import {
  main,
  esc,
  date,
  errorText,
  demoNotice,
  page,
  back,
  tabs,
  gated,
} from "../components/index.js";

import {
  cfg,
} from "../api/client.js";

import {
  currentUser,
} from "../api/auth.js";

import {
  getHistory,
  getTrends,
} from "../api/history.js";

import {
  labs,
} from "../data/catalog.js";

import {
  state,
} from "../state.js";


// ============================================================
// HELPERS
// ============================================================


function featureLabel(
  series,
) {
  return (
    series.label ||
    labs[
      series.feature
    ]?.label ||
    series.feature
  );
}


function formatValue(
  value,
) {
  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return Number(
    value,
  ).toLocaleString(
    "ru-RU",
    {
      maximumFractionDigits:
        3,
    },
  );
}


function finite(
  value,
) {
  return Number.isFinite(
    Number(
      value,
    ),
  );
}


// ============================================================
// REFERENCE
// ============================================================


function getReferenceRange(
  series,
  points,
) {
  let low =
    finite(
      series.reference_low,
    )
      ? Number(
          series.reference_low,
        )
      : null;


  let high =
    finite(
      series.reference_high,
    )
      ? Number(
          series.reference_high,
        )
      : null;


  if (
    low === null
  ) {
    const point =
      points.find(
        (
          item,
        ) =>
          finite(
            item.reference_low,
          ),
      );


    if (
      point
    ) {
      low =
        Number(
          point.reference_low,
        );
    }
  }


  if (
    high === null
  ) {
    const point =
      points.find(
        (
          item,
        ) =>
          finite(
            item.reference_high,
          ),
      );


    if (
      point
    ) {
      high =
        Number(
          point.reference_high,
        );
    }
  }


  return {
    low,
    high,
  };
}


// ============================================================
// CHART
// ============================================================


function renderChart(
  series,
) {
  const points =
    (
      series.points ||
      []
    )
      .filter(
        (
          point,
        ) =>
          finite(
            point.value,
          ),
      )
      .map(
        (
          point,
        ) => ({
          ...point,

          value:
            Number(
              point.value,
            ),
        }),
      )
      .sort(
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


  const title =
    featureLabel(
      series,
    );


  const unit =
    series.unit ||
    "";


  if (
    !points.length
  ) {
    return `
      <article class="chart-card">

        <h3>
          ${
            esc(
              title,
            )
          }
        </h3>

        <p>
          Измерений пока нет.
        </p>

      </article>
    `;
  }


  const {
    low:
      referenceLow,

    high:
      referenceHigh,
  } =
    getReferenceRange(
      series,
      points,
    );


  const referenceValues =
    [
      referenceLow,
      referenceHigh,
    ].filter(
      (
        value,
      ) =>
        finite(
          value,
        ),
    );


  const allValues = [
    ...points.map(
      (
        point,
      ) =>
        point.value,
    ),

    ...referenceValues,
  ];


  let minimum =
    Math.min(
      ...allValues,
    );


  let maximum =
    Math.max(
      ...allValues,
    );


  if (
    minimum === maximum
  ) {
    const delta =
      Math.max(
        Math.abs(
          maximum,
        ) *
          0.1,

        1,
      );


    minimum -=
      delta;


    maximum +=
      delta;

  } else {
    const padding =
      Math.max(
        (
          maximum -
          minimum
        ) *
          0.18,

        Math.abs(
          maximum,
        ) *
          0.05,

        0.5,
      );


    minimum =
      Math.max(
        0,
        minimum -
          padding,
      );


    maximum +=
      padding;
  }


  const left =
    60;


  const right =
    470;


  const top =
    25;


  const bottom =
    195;


  const x =
    (
      index,
    ) => {

      if (
        points.length ===
        1
      ) {
        return (
          left +
          right
        ) /
          2;
      }


      return (
        left +
        (
          index /
          (
            points.length -
            1
          )
        ) *
          (
            right -
            left
          )
      );
    };


  const y =
    (
      value,
    ) =>
      bottom -
      (
        (
          value -
          minimum
        ) /
        (
          maximum -
          minimum
        )
      ) *
        (
          bottom -
          top
        );


  const grid =
    Array.from(
      {
        length:
          5,
      },

      (
        _,
        index,
      ) => {

        const value =
          minimum +
          (
            (
              maximum -
              minimum
            ) *
            index
          ) /
            4;


        const py =
          y(
            value,
          );


        return `
          <line
            x1="${left}"
            x2="${right}"
            y1="${py}"
            y2="${py}"
            stroke="#dce5e8"
          />

          <text
            x="${
              left -
              8
            }"
            y="${
              py +
              4
            }"
            text-anchor="end"
            font-size="11"
            fill="#516672"
          >
            ${
              formatValue(
                value,
              )
            }
          </text>
        `;
      },
    ).join(
      "",
    );


  let referenceArea =
    "";


  if (
    finite(
      referenceLow,
    ) &&
    finite(
      referenceHigh,
    )
  ) {
    const topY =
      y(
        Number(
          referenceHigh,
        ),
      );


    const bottomY =
      y(
        Number(
          referenceLow,
        ),
      );


    referenceArea = `
      <rect
        x="${left}"
        y="${
          Math.min(
            topY,
            bottomY,
          )
        }"
        width="${
          right -
          left
        }"
        height="${
          Math.abs(
            bottomY -
            topY,
          )
        }"
        fill="#0deacf16"
      />
    `;
  }


  const referenceLines =
    [
      {
        value:
          referenceLow,

        label:
          "нижняя",
      },

      {
        value:
          referenceHigh,

        label:
          "верхняя",
      },
    ]
      .filter(
        (
          item,
        ) =>
          finite(
            item.value,
          ),
      )
      .map(
        (
          item,
        ) => {

          const py =
            y(
              Number(
                item.value,
              ),
            );


          return `
            <line
              x1="${left}"
              x2="${right}"
              y1="${py}"
              y2="${py}"
              stroke="#255c60"
              stroke-dasharray="5 4"
            />

            <text
              x="${
                right -
                2
              }"
              y="${
                py -
                6
              }"
              text-anchor="end"
              font-size="10"
              fill="#255c60"
            >
              ${
                item.label
              }:
              ${
                formatValue(
                  item.value,
                )
              }
            </text>
          `;
        },
      )
      .join(
        "",
      );


  const polyline =
    points.length >
      1
      ? `
        <polyline
          points="${
            points
              .map(
                (
                  point,
                  index,
                ) =>
                  `${
                    x(
                      index,
                    )
                  },${
                    y(
                      point.value,
                    )
                  }`,
              )
              .join(
                " ",
              )
          }"
          fill="none"
          stroke="#0abba5"
          stroke-width="2.5"
        />
      `
      : "";


  const circles =
    points
      .map(
        (
          point,
          index,
        ) => {

          const px =
            x(
              index,
            );


          const py =
            y(
              point.value,
            );


          return `
            <circle
              cx="${px}"
              cy="${py}"
              r="5"
              fill="#0abba5"
            >

              <title>
                ${
                  esc(
                    date(
                      point.date,
                    ),
                  )
                }:
                ${
                  esc(
                    formatValue(
                      point.value,
                    ),
                  )
                }
                ${
                  esc(
                    unit,
                  )
                }
              </title>

            </circle>
          `;
        },
      )
      .join(
        "",
      );


  const dateLabels =
    points
      .map(
        (
          point,
          index,
        ) => {

          const show =
            points.length <=
              5 ||
            index ===
              0 ||
            index ===
              points.length -
                1;


          if (
            !show
          ) {
            return "";
          }


          return `
            <text
              x="${
                x(
                  index,
                )
              }"
              y="222"
              text-anchor="middle"
              font-size="10"
              fill="#516672"
            >
              ${
                esc(
                  date(
                    point.date,
                  ),
                )
              }
            </text>
          `;
        },
      )
      .join(
        "",
      );


  const referenceSources =
    [
      ...new Set(
        points
          .map(
            (
              point,
            ) =>
              point.reference_source,
          )
          .filter(
            Boolean,
          ),
      ),
    ];


  return `
    <article class="chart-card">

      <div
        style="
          display:flex;
          justify-content:space-between;
          gap:12px;
          align-items:flex-start
        "
      >

        <div>

          <h3>
            ${
              esc(
                title,
              )
            }
          </h3>

          <p class="hint">
            ${
              points.length
            }
            ${
              points.length ===
              1
                ? "измерение"
                : "измерений"
            }
          </p>

        </div>


        ${
          unit
            ? `
              <span class="tag">
                ${
                  esc(
                    unit,
                  )
                }
              </span>
            `
            : ""
        }

      </div>


      <svg
        class="chart"
        viewBox="0 0 500 240"
        role="img"
        aria-label="Динамика ${esc(
          title,
        )}"
      >

        <title>
          Динамика
          ${
            esc(
              title,
            )
          }
        </title>

        ${grid}

        ${referenceArea}

        ${referenceLines}

        ${polyline}

        ${circles}

        ${dateLabels}

      </svg>


      <div class="legend">

        <span>
          ● Измеренное значение
        </span>

        ${
          referenceValues.length
            ? `
              <span>
                ┄ Референсные границы
              </span>
            `
            : `
              <span>
                Референсный диапазон
                не предоставлен
              </span>
            `
        }

      </div>


      <details
        style="margin-top:16px"
      >

        <summary>
          Все измерения
        </summary>


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

                      const pointLow =
                        finite(
                          point.reference_low,
                        )
                          ? Number(
                              point.reference_low,
                            )
                          : referenceLow;


                      const pointHigh =
                        finite(
                          point.reference_high,
                        )
                          ? Number(
                              point.reference_high,
                            )
                          : referenceHigh;


                      let reference =
                        "—";


                      if (
                        finite(
                          pointLow,
                        ) &&
                        finite(
                          pointHigh,
                        )
                      ) {
                        reference =
                          `${formatValue(
                            pointLow,
                          )}–${formatValue(
                            pointHigh,
                          )}`;

                      } else if (
                        finite(
                          pointLow,
                        )
                      ) {
                        reference =
                          `≥ ${formatValue(
                            pointLow,
                          )}`;

                      } else if (
                        finite(
                          pointHigh,
                        )
                      ) {
                        reference =
                          `≤ ${formatValue(
                            pointHigh,
                          )}`;
                      }


                      return `
                        <tr>

                          <td>
                            ${
                              esc(
                                date(
                                  point.date,
                                ),
                              )
                            }
                          </td>

                          <td>
                            ${
                              esc(
                                formatValue(
                                  point.value,
                                ),
                              )
                            }

                            ${
                              esc(
                                unit,
                              )
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

      </details>


      ${
        referenceSources.length
          ? `
            <p
              class="hint"
              style="margin-top:12px"
            >
              Референс:
              ${
                referenceSources
                  .map(
                    (
                      source,
                    ) =>
                      esc(
                        source,
                      ),
                  )
                  .join(
                    "; ",
                  )
              }
            </p>
          `
          : ""
      }

    </article>
  `;
}


// ============================================================
// GROUP
// ============================================================


function renderGroup(
  group,
) {
  const series =
    (
      group.series ||
      []
    ).filter(
      (
        item,
      ) =>
        item.points
          ?.length,
    );


  if (
    !series.length
  ) {
    return "";
  }


  return `
    <section
      style="margin-top:40px"
    >

      <div class="result-top">

        <div>

          <span class="eyebrow">
            ${
              esc(
                group.key,
              )
            }
          </span>

          <h2
            style="margin-top:10px"
          >
            ${
              esc(
                group.label,
              )
            }
          </h2>

        </div>

      </div>


      <div class="split">

        ${
          series
            .map(
              renderChart,
            )
            .join(
              "",
            )
        }

      </div>

    </section>
  `;
}


// ============================================================
// DEMO
// ============================================================


async function buildDemoGroups() {
  const items =
    await getHistory();


  const map =
    {};


  for (
    const item
    of items
  ) {
    for (
      const lab
      of item.labs ||
        []
    ) {
      if (
        lab.value ===
          null ||
        lab.value ===
          undefined
      ) {
        continue;
      }


      const feature =
        lab.code;


      map[
        feature
      ] ??= {
        feature,

        label:
          labs[
            feature
          ]?.label ||
          feature,

        unit:
          lab.unit ||
          null,

        reference_low:
          null,

        reference_high:
          null,

        points:
          [],
      };


      map[
        feature
      ].points.push({
        screening_id:
          item.id ||
          item.screening_id ||
          "demo",

        date:
          item.created_at,

        value:
          lab.value,

        reference_low:
          null,

        reference_high:
          null,

        reference_source:
          null,
      });
    }
  }


  return [
    {
      key:
        "demo",

      label:
        "Лабораторные показатели",

      series:
        Object.values(
          map,
        ),
    },
  ];
}


// ============================================================
// PAGE
// ============================================================


export async function trendsPage() {
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
  // AUTH
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
        Динамика показателей
      </h1>

      <p class="subtitle">
        Загружаем лабораторную историю…
      </p>

      ${tabs(
        "trends",
      )}

      <p role="status">
        <span class="loader"></span>
        Загружаем измерения…
      </p>
      `,
    );


  try {
    let groups;


    if (
      cfg.mode ===
      "demo"
    ) {
      groups =
        await buildDemoGroups();

    } else {
      const response =
        await getTrends();


      groups =
        response?.groups;


      if (
        !Array.isArray(
          groups,
        )
      ) {
        throw new Error(
          "Ответ динамики не соответствует формату API.",
        );
      }
    }


    if (
      version !==
      state.routeVersion
    ) {
      return;
    }


    const nonEmptyGroups =
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


    main.innerHTML =
      page(
        `
        ${back()}


        <div class="result-top">

          <div>

            <h1>
              Динамика показателей
            </h1>

            <p class="subtitle">
              Изменение лабораторных
              показателей между обследованиями
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
          "trends",
        )}


        ${demoNotice()}


        <div class="notice">

          <span aria-hidden="true">
            ⓘ
          </span>

          <p>
            <strong>
              Референсные границы
              берутся из сохранённых
              лабораторных данных.
            </strong>

            <br>

            Они могут отличаться
            между лабораториями,
            поэтому Meditron
            не подставляет их
            самостоятельно.
          </p>

        </div>


        ${
          nonEmptyGroups.length
            ? nonEmptyGroups
                .map(
                  renderGroup,
                )
                .join(
                  "",
                )
            : `
              <div class="empty">

                <h3>
                  Недостаточно данных
                  для динамики
                </h3>

                <p>
                  Проведите несколько
                  скринингов, чтобы
                  сравнивать лабораторные
                  показатели во времени.
                </p>

                <a
                  href="#/screening"
                  class="btn"
                >
                  Новый скрининг →
                </a>

              </div>
            `
        }
        `,
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
          Динамика показателей
        </h1>

        ${tabs(
          "trends",
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
          id="retry-trends"
          class="btn secondary"
          type="button"
        >
          Повторить
        </button>
        `,
      );


    document
      .querySelector(
        "#retry-trends",
      )
      ?.addEventListener(
        "click",
        trendsPage,
      );
  }
}
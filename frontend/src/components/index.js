import { state } from "../state.js";
import { cfg } from "../api/client.js";
import { currentUser, logout } from "../api/auth.js";
import { labs, conditions } from "../data/catalog.js";
const main = document.querySelector("main");
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const pct = (n) =>
  `${(Number(n) * 100).toLocaleString("ru-RU", { maximumFractionDigits: 1 })}%`;
const date = (d) => new Date(d).toLocaleDateString("ru-RU");
const name = (c) => conditions[c] || c;
function toast(text) {
  const t = document.querySelector("#toast");
  t.textContent = text;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 4000);
}
function errorText(
  error,
) {
  if (
    error?.status ===
    401
  ) {
    void logout();
  }

  if (
    error?.details &&
    typeof error.details ===
      "string"
  ) {
    return esc(
      error.details,
    );
  }

  return esc(
    error?.message ||
      "Произошла ошибка. Повторите попытку.",
  );
}
function shell(route) {
  document.querySelector("#header").innerHTML =
    `<div class="container topbar"><a class="brand" href="#/" aria-label="Meditron — главная"><img src="assets/sechenov.svg" alt="Сеченовский университет"><span class="wordmark">meditron<span style="color:#0abba5">.</span></span></a><button class="menu-toggle" aria-label="Открыть меню" aria-expanded="false">Меню ☰</button><nav aria-label="Основная навигация"><a href="#/about" class="${route === "about" ? "active" : ""}">О сервисе</a><a href="#/how">Как это работает</a><a href="#/history" class="${route === "history" ? "active" : ""}">История</a><a href="#/profile">${currentUser ? "Мой кабинет" : "Войти"}</a><a href="#/screening" class="btn small">Начать скрининг <span>↗</span></a></nav></div><div class="modebar"><div class="container"><span><i class="dot"></i>${cfg.mode === "demo" ? "Демонстрационный режим · используются тестовые ответы" : "Подключение к API · результаты предоставляет сервер"}</span><a href="#/connection" class="link">${cfg.mode === "demo" ? "Настроить API" : "Подключение"}</a></div></div>`;
  document.querySelector(".menu-toggle").onclick = (e) => {
    const open = document.querySelector("nav").classList.toggle("open");
    e.currentTarget.setAttribute("aria-expanded", String(open));
  };
  document.querySelector("#footer").innerHTML =
    `<div class="footer"><div class="container"><div class="footer-grid"><div><a href="#/"><img src="assets/sechenov.svg" alt="Сеченовский университет"></a><p>Meditron — проект хакатона.<br>ИИ-скрининг латентных дефицитных состояний по лабораторным данным.</p></div><div><h3>Навигация</h3><a href="#/about">О сервисе</a><a href="#/how">Как это работает</a><a href="#/screening">Новый скрининг</a><a href="#/doctor">Для врача</a></div><div><h3>Личный кабинет</h3><a href="#/history">История анализов</a><a href="#/trends">Динамика показателей</a><a href="#/privacy">Обработка данных</a><a href="#/connection">Подключение API</a></div></div><div class="footer-bottom"><span>© 2026 Meditron · Скрининг не заменяет консультацию врача</span><a href="https://design.sechenov.ru/color-medicine" target="_blank" rel="noopener">Дизайн-система Сеченовского университета ↗</a></div></div></div>`;
}
const medicalNotice = () =>
  `<div class="notice"><span aria-hidden="true">ⓘ</span><p><strong>Это скрининг, а не диагноз.</strong><br>Результат помогает обратить внимание на возможные дефицитные состояния. Для интерпретации анализов обратитесь к врачу.</p></div>`;
const demoNotice = () =>
  cfg.mode === "demo"
    ? `<div class="notice"><span>◈</span><p><strong>Демонстрационные данные</strong><br>Ответ модели заранее задан и не зависит от введённых значений. История в этом режиме существует только до обновления страницы.</p></div>`
    : "";
const page = (html) => `<div class="container page">${html}</div>`;
const back = () => `<a class="back" href="#/">← На главную</a>`;
const tabs = (active) =>
  `<div class="tabs"><a href="#/profile" class="${active === "profile" ? "active" : ""}">Кабинет</a><a href="#/history" class="${active === "history" ? "active" : ""}">История</a><a href="#/trends" class="${active === "trends" ? "active" : ""}">Динамика</a></div>`;
function steps() {
  return `<div class="steps">${[
    [
      "01",
      "Введите данные",
      "Перенесите доступные показатели из лабораторного бланка.",
    ],
    ["02", "Запустите скрининг", "Данные передаются серверу для обработки."],
    ["03", "Изучите результат", "Посмотрите оценки модели и предупреждения."],
    [
      "04",
      "Следите за динамикой",
      "Сравнивайте измерения в истории своего кабинета.",
    ],
  ]
    .map(
      ([n, t, d]) =>
        `<article class="step"><span>${n} /</span><h3>${t}</h3><p>${d}</p></article>`,
    )
    .join("")}</div>`;
}
function faq() {
  return [
    [
      "Является ли результат диагнозом?",
      "Нет. Это результат автоматизированного скрининга. Он не заменяет оценку врача и не используется для самостоятельного назначения лечения.",
    ],
    [
      "Нужно ли заполнять все показатели?",
      "Нет. Введите доступные данные. Пустые поля не превращаются в нули; достаточность данных оценивает сервер.",
    ],
    [
      "Что означает процент в результате?",
      "Это значение, которое вернула модель. Без отдельной проверки калибровки оно не является подтверждённой вероятностью заболевания.",
    ],
    [
      "Как используются мои данные?",
      "В демонстрационном режиме данные существуют в памяти текущей страницы. При подключении API они отправляются указанному серверу; условия хранения определяет ваш бэкенд.",
    ],
    [
      "Можно ли загрузить файл?",
      "Врач может предварительно просмотреть CSV. Пакетная отправка подключается после согласования маршрута и формата с командой API.",
    ],
  ]
    .map(([q, a]) => `<details><summary>${q}</summary><p>${a}</p></details>`)
    .join("");
}
function labTable(values) {
  return `<div class="table-wrap"><table><thead><tr><th>Показатель</th><th>Значение</th><th>Единица</th></tr></thead><tbody>${values
    .filter((v) => v.value !== null)
    .map(
      (v) =>
        `<tr><td>${esc(labs[v.code]?.[0] || v.code)}</td><td>${esc(v.value)}</td><td>${esc(v.unit)}</td></tr>`,
    )
    .join("")}</tbody></table></div>`;
}
function download(filename, content, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function gated() {
  if (cfg.mode !== "demo" && !currentUser) {
    main.innerHTML = page(
      `<div class="empty"><h1>Войдите в аккаунт</h1><p>Для просмотра личных результатов нужна авторизация.</p><a href="#/login" class="btn">Войти →</a></div>`,
    );
    return true;
  }
  return false;
}
function chart(t) {
  const points = t.points
    .filter((p) => Number.isFinite(p.value))
    .sort((a, b) => new Date(a.date) - new Date(b.date));
  if (!points.length)
    return `<div class="chart-card"><h3>${esc(labs[t.code]?.[0] || t.code)}</h3><p>Измерений пока нет.</p></div>`;
  const refs = [t.reference_low, t.reference_high].filter(Number.isFinite);
  const vals = [...points.map((p) => p.value), ...refs];
  let lo = Math.min(...vals),
    hi = Math.max(...vals);
  const pad = Math.max((hi - lo) * 0.2, Math.abs(hi) * 0.08, 1);
  lo = Math.max(0, lo - pad);
  hi += pad;
  const x = (p) => {
    const start = new Date(points[0].date).getTime(),
      end = new Date(points.at(-1).date).getTime();
    return end === start
      ? 260
      : 55 + ((new Date(p.date).getTime() - start) / (end - start)) * 410;
  };
  const y = (v) => 195 - ((v - lo) / (hi - lo)) * 155;
  const svg = `<svg class="chart" viewBox="0 0 500 240" role="img" aria-label="Динамика ${esc(labs[t.code]?.[0] || t.code)}"><title>${esc(labs[t.code]?.[0] || t.code)}</title>${Array.from(
    { length: 4 },
    (_, i) => {
      const v = lo + ((hi - lo) * i) / 3;
      return `<line x1="55" x2="470" y1="${y(v)}" y2="${y(v)}" stroke="#dce5e8"/><text x="45" y="${y(v) + 4}" text-anchor="end" font-size="11" fill="#516672">${v.toLocaleString("ru-RU", { maximumFractionDigits: 1 })}</text>`;
    },
  ).join(
    "",
  )}${Number.isFinite(t.reference_low) && Number.isFinite(t.reference_high) ? `<rect x="55" y="${y(t.reference_high)}" width="415" height="${Math.max(0, y(t.reference_low) - y(t.reference_high))}" fill="#0deacf16"/>` : ""}${refs.map((v, i) => `<line x1="55" x2="470" y1="${y(v)}" y2="${y(v)}" stroke="#255c60" stroke-dasharray="5 4"/><text x="468" y="${y(v) - 5}" font-size="10" fill="#255c60" text-anchor="end">${i === 0 && Number.isFinite(t.reference_low) ? "нижняя" : "верхняя"}: ${v}</text>`).join("")}<polyline points="${points.map((p) => `${x(p)},${y(p.value)}`).join(" ")}" fill="none" stroke="#0abba5" stroke-width="2.5"/>${points.map((p, i) => `<circle cx="${x(p)}" cy="${y(p.value)}" r="4.5" fill="#0abba5"><title>${date(p.date)}: ${p.value} ${esc(t.unit)}</title></circle>${i === 0 || i === points.length - 1 ? `<text x="${x(p)}" y="220" text-anchor="middle" font-size="11" fill="#516672">${date(p.date)}</text>` : ""}`).join("")}</svg>`;
  return `<article class="chart-card"><div style="display:flex;justify-content:space-between;gap:12px"><h3>${esc(labs[t.code]?.[0] || t.code)}</h3><span class="tag">${esc(t.unit)}</span></div>${svg}<div class="legend"><span>● Измеренное значение</span>${refs.length ? `<span>┄ ${cfg.mode === "demo" ? "Условные границы примера" : "Референсные границы"}</span>` : "<span>Референсный диапазон не предоставлен</span>"}</div><details style="margin-top:16px;font-size:13px"><summary>Все измерения</summary><table><tbody>${points.map((p) => `<tr><td>${date(p.date)}</td><td>${p.value} ${esc(t.unit)}</td></tr>`).join("")}</tbody></table></details>${t.reference_source ? `<p class="hint" style="margin-top:12px">${esc(t.reference_source)}</p>` : ""}</article>`;
}
function parseCSV(text) {
  const delimiter = text.split(/\r?\n/)[0].includes(";") ? ";" : ",";
  const rows = [];
  let row = [],
    cell = "",
    quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      if (quoted && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else quoted = !quoted;
    } else if (c === delimiter && !quoted) {
      row.push(cell);
      cell = "";
    } else if ((c === "\n" || c === "\r") && !quoted) {
      if (c === "\r" && text[i + 1] === "\n") i++;
      row.push(cell);
      if (row.some((v) => v.trim())) rows.push(row);
      row = [];
      cell = "";
    } else cell += c;
  }
  if (quoted) throw Error("CSV содержит незакрытую кавычку.");
  row.push(cell);
  if (row.some((v) => v.trim())) rows.push(row);
  return rows;
}
export {
  main,
  esc,
  pct,
  date,
  name,
  toast,
  errorText,
  shell,
  medicalNotice,
  demoNotice,
  page,
  back,
  tabs,
  steps,
  faq,
  labTable,
  download,
  gated,
  chart,
  parseCSV,
};

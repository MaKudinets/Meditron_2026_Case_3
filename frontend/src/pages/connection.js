import {
  main,
  toast,
  errorText,
  shell,
  page,
  back,
} from "../components/index.js";
import { cfg, health } from "../api/client.js";
import { logout } from "../api/auth.js";
import { state } from "../state.js";
export function connection() {
  main.innerHTML = page(
    `${back()}<div class="config"><h1>Подключение API</h1><p class="subtitle">Настройки интеграции для команды проекта</p><div class="notice"><p>Схемы и маршруты взяты из приложенного плана и требуют сверки с FastAPI /docs. Настройки действуют до обновления страницы. Постоянные значения задаются в src/config.js.</p></div><form id="connection-form"><div class="field"><label for="mode">Режим работы</label><select id="mode"><option value="demo">Демонстрация с тестовыми ответами</option><option value="live">Настоящий API</option></select></div><div class="field"><label for="api-url">Базовый адрес API</label><input id="api-url" type="url" placeholder="https://api.example.org"></div><div class="field"><label for="request-format">Формат лабораторных данных</label><select id="request-format"><option value="labs">labs: [{code, value, unit}]</option><option value="features">features: {code: value}</option></select></div><div class="field"><label for="screening-endpoint">Endpoint скрининга</label><input id="screening-endpoint" required></div><div id="connection-status" role="status"></div><div class="actions"><button type="submit" class="btn">Применить настройки →</button><button type="button" id="health" class="btn secondary">Проверить /health</button></div></form><p class="hint" style="margin-top:24px">Для опубликованного сайта используйте HTTPS API и добавьте origin сайта в CORS. HTTP localhost можно использовать при локальном запуске фронтенда.</p><div class="actions"><a class="link" href="INTEGRATION.md" target="_blank">Документация подключения ↗</a></div></div>`,
  );
  const f = document.querySelector("#connection-form");
  f.querySelector("#mode").value = cfg.mode;
  f.querySelector("#api-url").value = cfg.apiUrl;
  f.querySelector("#request-format").value = cfg.requestFormat;
  f.querySelector("#screening-endpoint").value = cfg.endpoints.screenings;
  function apply() {
    const base = f.querySelector("#api-url").value.trim();
    const mode = f.querySelector("#mode").value;
    const endpoint = f.querySelector("#screening-endpoint").value.trim();
    if (mode === "live" && !base) throw Error("Укажите адрес API.");
    if (base) {
      const url = new URL(base);
      if (!["http:", "https:"].includes(url.protocol))
        throw Error("Используйте HTTP или HTTPS URL.");
      if (location.protocol === "https:" && url.protocol !== "https:")
        throw Error("Для опубликованного сайта нужен API с HTTPS.");
    }
    if (
      !endpoint.startsWith("/") ||
      endpoint.startsWith("//") ||
      endpoint.includes("?") ||
      endpoint.includes("#")
    )
      throw Error(
        "Endpoint должен начинаться с одного / и не содержать параметры.",
      );
    logout();
    state.result = null;
    state.cachedHistory = [];
    state.formDraft = null;
    cfg.apiUrl = base.replace(/\/$/, "");
    cfg.mode = mode;
    cfg.requestFormat = f.querySelector("#request-format").value;
    cfg.endpoints.screenings = endpoint;
    shell("connection");
  }
  f.onsubmit = (e) => {
    e.preventDefault();
    try {
      apply();
      toast("Настройки применены.");
      location.hash = "/screening";
    } catch (e) {
      document.querySelector("#connection-status").innerHTML =
        `<div class="error">${errorText(e)}</div>`;
    }
  };
  document.querySelector("#health").onclick = async (e) => {
    const status = document.querySelector("#connection-status"),
      version = state.routeVersion;
    try {
      const url = f.querySelector("#api-url").value.trim();
      if (!url) throw Error("Укажите адрес API для проверки.");
      const parsed = new URL(url);
      if (
        !["http:", "https:"].includes(parsed.protocol) ||
        (location.protocol === "https:" && parsed.protocol !== "https:")
      )
        throw Error("Для опубликованного сайта нужен API с HTTPS.");
      const old = cfg.apiUrl;
      cfg.apiUrl = url;
      try {
        e.currentTarget.disabled = true;
        status.textContent = "Проверяем соединение…";
        const r = await health();
        if (version === state.routeVersion)
          status.textContent =
            r?.status === "ok"
              ? "Сервер доступен: status = ok"
              : "Сервер ответил, но формат /health отличается от ожидаемого.";
      } finally {
        cfg.apiUrl = old;
      }
    } catch (e) {
      if (version === state.routeVersion)
        status.innerHTML = `<div class="error">${errorText(e)}</div>`;
    } finally {
      if (version === state.routeVersion)
        document.querySelector("#health").disabled = false;
    }
  };
}

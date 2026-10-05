import {
  main,
  esc,
  demoNotice,
  page,
  back,
  tabs,
  gated,
} from "../components/index.js";
import { cfg } from "../api/client.js";
import { currentUser, logout } from "../api/auth.js";
import { state } from "../state.js";
export function profile() {
  if (gated()) return;
  main.innerHTML = page(
    `${back()}<h1>Личный кабинет</h1><p class="subtitle">${esc(currentUser?.email || "Демонстрационный профиль")}</p>${tabs("profile")}${demoNotice()}<div class="cards"><a href="#/screening" class="card"><div class="icon">+</div><h3>Новый скрининг ↗</h3><p>Введите данные нового обследования.</p></a><a href="#/history" class="card"><div class="icon">≡</div><h3>История анализов ↗</h3><p>Откройте предыдущие результаты.</p></a><a href="#/trends" class="card"><div class="icon">⌁</div><h3>Динамика ↗</h3><p>Посмотрите изменения показателей во времени.</p></a></div>${currentUser?.role === "doctor" || cfg.mode === "demo" ? '<div class="actions"><a href="#/doctor" class="btn secondary">Рабочее пространство врача ↗</a></div>' : ""}${currentUser ? '<div class="actions"><button id="logout" class="btn secondary">Выйти из аккаунта</button></div>' : ""}`,
  );
  document
  .querySelector(
    "#logout",
  )
  ?.addEventListener(
    "click",
    async () => {

      await logout();

      state.result =
        null;

      state.cachedHistory =
        [];

      state.formDraft =
        null;

      location.hash =
        "/";
    },
  );
}

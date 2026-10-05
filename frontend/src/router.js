import {
  home,
} from "./pages/home.js";

import {
  screening,
} from "./pages/screening.js";

import {
  results,
} from "./pages/results.js";

import {
  auth,
  verifyEmailPage,
  forgotPasswordPage,
  resetPasswordPage,
} from "./pages/auth.js";

import {
  profile,
} from "./pages/profile.js";

import {
  historyPage,
} from "./pages/historyPage.js";

import {
  trendsPage,
} from "./pages/trendsPage.js";

import {
  doctor,
} from "./pages/doctor.js";

import {
  connection,
} from "./pages/connection.js";

import {
  about,
} from "./pages/about.js";

import {
  privacy,
} from "./pages/privacy.js";

import {
  shell,
  back,
  page,
  steps,
  medicalNotice,
} from "./components/index.js";

import {
  beginRoute,
} from "./state.js";


const main =
  document.querySelector(
    "main",
  );


// ============================================================
// ROUTE PARSING
// ============================================================


function parseRoute() {
  const hash =
    location.hash.replace(
      /^#\/?/,
      "",
    );

  const [
    routePart,
    hashQuery = "",
  ] =
    hash.split("?");

  const route =
    routePart || "";

  const params =
    new URLSearchParams(
      hashQuery,
    );

  const pageParams =
    new URLSearchParams(
      location.search,
    );

  for (
    const [
      key,
      value,
    ]
    of pageParams.entries()
  ) {
    if (
      !params.has(
        key,
      )
    ) {
      params.set(
        key,
        value,
      );
    }
  }

  return {
    route,
    params,
  };
}


// ============================================================
// NORMAL URL -> HASH ROUTER
// ============================================================


export function normalizeAuthLinks() {
  const path =
    location.pathname;

  const query =
    location.search;


  if (
    path ===
    "/verify-email"
  ) {
    history.replaceState(
      null,
      "",
      `/#/verify-email${query}`,
    );

    return true;
  }


  if (
    path ===
    "/reset-password"
  ) {
    history.replaceState(
      null,
      "",
      `/#/reset-password${query}`,
    );

    return true;
  }


  return false;
}


// ============================================================
// ROUTER
// ============================================================


export async function route() {
  beginRoute();

  const {
    route:
      routeName,
    params,
  } =
    parseRoute();


  shell(
    routeName,
  );

  window.scrollTo(
    0,
    0,
  );


  const titles = {
    screening:
      "Новый скрининг",

    result:
      "Результат",

    history:
      "История",

    trends:
      "Динамика",

    login:
      "Вход",

    register:
      "Регистрация",

    profile:
      "Кабинет",

    doctor:
      "Для врача",

    connection:
      "Подключение API",

    about:
      "О сервисе",

    privacy:
      "Обработка данных",

    how:
      "Как это работает",

    "verify-email":
      "Подтверждение email",

    "forgot-password":
      "Восстановление пароля",

    "reset-password":
      "Новый пароль",
  };


  document.title =
    `${
      titles[
        routeName
      ] ||
      "ИИ-скрининг"
    } — Meditron`;


  switch (
    routeName
  ) {
    case "":
      home();
      break;


    case "screening":
      screening();
      break;


    case "result":
      results();
      break;


    case "about":
      about();
      break;


    case "how":
      main.innerHTML =
        page(
          `
          ${back()}

          <h1>
            Как это работает
          </h1>

          <p class="subtitle">
            От лабораторного бланка
            до понятного результата
          </p>

          ${steps()}

          ${medicalNotice()}

          <a
            class="btn"
            href="#/screening"
          >
            Начать скрининг →
          </a>
          `,
        );
      break;


    case "login":
      auth();
      break;


    case "register":
      auth(
        true,
      );
      break;


    case "verify-email":
      verifyEmailPage(
        params,
      );
      break;


    case "forgot-password":
      forgotPasswordPage();
      break;


    case "reset-password":
      resetPasswordPage(
        params,
      );
      break;


    case "profile":
      profile();
      break;


    case "history":
      await historyPage();
      break;


    case "trends":
      await trendsPage();
      break;


    case "doctor":
      doctor();
      break;


    case "connection":
      connection();
      break;


    case "privacy":
      privacy();
      break;


    default:
      main.innerHTML =
        page(
          `
          <div class="empty">

            <h1>
              Страница не найдена
            </h1>

            <p>
              Проверьте адрес
              или вернитесь
              на главную.
            </p>

            <a
              class="btn"
              href="#/"
            >
              На главную →
            </a>

          </div>
          `,
        );
  }
}


window.addEventListener(
  "hashchange",
  route,
);
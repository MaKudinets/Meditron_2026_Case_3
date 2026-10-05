import {
  main,
  toast,
  errorText,
  page,
} from "../components/index.js";

import {
  cfg,
} from "../api/client.js";

import {
  login,
  register,
  verifyEmail,
  resendVerification,
  forgotPassword,
  resetPassword,
} from "../api/auth.js";

import {
  state,
} from "../state.js";


// ============================================================
// COMMON AUTH LAYOUT
// ============================================================


function authLayout(
  content,
) {
  main.innerHTML = page(
    `
    <div class="auth-layout">

      <div class="auth-art">

        <div class="eyebrow">
          Meditron / личный кабинет
        </div>

        <img
          src="assets/robot-login.png"
          alt="Робот Meditron за ноутбуком"
        >

        <div>
          <h2>
            <span style="color:#0DEACF;">Ваше здоровье.</span><br>
            Ваша история.
          </h2>

          <p
            style="
            color:#344054;
            margin-top:18px
          "
          >
            Результаты обследований
            и динамика показателей
            в одном месте.
          </p>
        </div>

      </div>

      ${content}

    </div>
    `,
  );
}


// ============================================================
// LOGIN / REGISTER
// ============================================================


export function auth(
  registerPage = false,
) {
  authLayout(
    `
    <form
      class="auth-form"
      id="auth-form"
    >

      <h1>
        ${
          registerPage
            ? "Создать аккаунт"
            : "С возвращением"
        }
      </h1>

      <p class="subtitle">
        ${
          cfg.mode === "demo"
            ? "В демонстрационном режиме аккаунт не создаётся на сервере."
            : registerPage
              ? "Создайте аккаунт пациента или врача."
              : "Войдите, чтобы открыть личный кабинет."
        }
      </p>

      <div class="field">
        <label for="email">
          Email
        </label>

        <input
          id="email"
          name="email"
          type="email"
          required
          autocomplete="email"
          placeholder="you@example.com"
        >
      </div>

      <div class="field">
        <label for="password">
          Пароль
        </label>

        <input
          id="password"
          name="password"
          type="password"
          required
          ${
            registerPage
              ? 'minlength="8"'
              : ""
          }
          autocomplete="${
            registerPage
              ? "new-password"
              : "current-password"
          }"
          placeholder="${
            registerPage
              ? "Не менее 8 символов"
              : "Введите пароль"
          }"
        >
      </div>

      ${
        registerPage
          ? `
            <div class="field">
              <label for="repeat">
                Повторите пароль
              </label>

              <input
                id="repeat"
                name="repeat"
                type="password"
                required
                minlength="8"
                autocomplete="new-password"
              >
            </div>

            <div class="field">
              <label for="role">
                Тип аккаунта
              </label>

              <select
                id="role"
                name="role"
                required
              >
                <option value="patient">
                  Пациент
                </option>

                <option value="doctor">
                  Врач
                </option>
              </select>
            </div>

            <label class="check privacy-check">
              <input
                type="checkbox"
                required
              >

              <span>
                Я ознакомился и соглашаюсь с
                <a
                  class="link"
                  href="/privacy-policy.pdf"
                  target="_blank"
                  rel="noopener"
                >
                  Политикой конфиденциальности
                </a>.
              </span>
            </label>

            <label class="check privacy-check">
              <input
                type="checkbox"
                required
              >

              <span>
                Я даю отдельное согласие на обработку результатов лабораторных анализов и сведений о состоянии здоровья для выполнения скрининга.
              </span>
            </label>
          `
          : ""
      }

      <div
        id="auth-error"
        role="alert"
      ></div>

      <button
        class="btn"
        type="submit"
      >
        ${
          registerPage
            ? "Создать аккаунт"
            : "Войти"
        }
        →
      </button>

      ${
        !registerPage
          ? `
            <p
              class="auth-switch"
              style="margin-top:12px"
            >
              <a
                href="#/forgot-password"
              >
                Забыли пароль?
              </a>
            </p>
          `
          : ""
      }

      <p class="auth-switch">

        ${
          registerPage
            ? `
              Уже есть аккаунт?
              <a href="#/login">
                Войти
              </a>
            `
            : `
              Нет аккаунта?
              <a href="#/register">
                Зарегистрироваться
              </a>
            `
        }

      </p>

      ${
        cfg.mode === "demo"
          ? `
            <p class="hint">
              Демовход проверяет только
              заполнение формы.
            </p>
          `
          : ""
      }

    </form>
    `,
  );


  document
    .querySelector(
      "#auth-form",
    )
    .onsubmit =
      async (
        event,
      ) => {

        event
          .preventDefault();

        const form =
          event.currentTarget;

        const version =
          state.routeVersion;

        const button =
          form.querySelector(
            "button[type=submit]",
          );

        const error =
          document.querySelector(
            "#auth-error",
          );

        error.innerHTML =
          "";


        if (
          registerPage &&
          form.elements.namedItem(
            "password",
          ).value !==
            form.elements.namedItem(
              "repeat",
            ).value
        ) {
          error.innerHTML =
            `
            <div class="error">
              Пароли не совпадают.
            </div>
            `;

          return;
        }


        button.disabled =
          true;

        button.innerHTML =
          `
          <span class="loader"></span>
          Подождите…
          `;


        try {
          const data = {
            email:
              form.elements.namedItem(
                "email",
              ).value.trim(),

            password:
              form.elements.namedItem(
                "password",
              ).value,
          };


          if (
            registerPage
          ) {
            data.role =
              form.elements.namedItem(
                "role",
              ).value;

            const response =
              await register(
                data,
              );

            if (
              version !==
              state.routeVersion
            ) {
              return;
            }

            if (
              response?.email_sent ===
              false
            ) {
              toast(
                "Аккаунт создан, но письмо подтверждения отправить не удалось.",
              );
            } else {
              toast(
                "Аккаунт создан. Подтвердите email перед входом.",
              );
            }

            location.hash =
              `/verify-email?email=${encodeURIComponent(
                data.email,
              )}`;

          } else {
            const user =
              await login(
                data,
              );

            if (
              version !==
              state.routeVersion
            ) {
              return;
            }

            if (
              user?.role ===
              "doctor"
            ) {
              location.hash =
                "/doctor";
            } else {
              location.hash =
                "/profile";
            }
          }

        } catch (errorValue) {
          if (
            version ===
            state.routeVersion
          ) {
            error.innerHTML =
              `
              <div class="error">
                ${
                  errorText(
                    errorValue,
                  )
                }
              </div>
              `;
          }

        } finally {
          if (
            version ===
            state.routeVersion
          ) {
            button.disabled =
              false;

            button.textContent =
              registerPage
                ? "Создать аккаунт →"
                : "Войти →";
          }
        }
      };
}


// ============================================================
// VERIFY EMAIL PAGE
// ============================================================


export function verifyEmailPage(
  params,
) {
  const token =
    params.get(
      "token",
    );

  const email =
    params.get(
      "email",
    );


  authLayout(
    `
    <div class="auth-form">

      <h1>
        Подтверждение email
      </h1>

      <p class="subtitle">
        Подтвердите адрес электронной почты,
        чтобы войти в аккаунт.
      </p>

      <div
        id="verify-status"
      >
        ${
          token
            ? `
              <p>
                Проверяем ссылку подтверждения…
              </p>
            `
            : `
              <p>
                Откройте ссылку,
                которую Meditron отправил
                на вашу почту.
              </p>
            `
        }
      </div>

      ${
        email
          ? `
            <button
              class="btn secondary"
              id="resend-verification"
              type="button"
            >
              Отправить письмо повторно
            </button>
          `
          : ""
      }

      <div
        id="verify-error"
        role="alert"
      ></div>

      <p class="auth-switch">
        <a href="#/login">
          Перейти ко входу
        </a>
      </p>

    </div>
    `,
  );


  if (
    token
  ) {
    runVerification(
      token,
    );
  }


  document
    .querySelector(
      "#resend-verification",
    )
    ?.addEventListener(
      "click",
      async (
        event,
      ) => {

        const button =
          event.currentTarget;

        const error =
          document.querySelector(
            "#verify-error",
          );

        error.innerHTML =
          "";

        button.disabled =
          true;


        try {
          await resendVerification(
            email,
          );

          toast(
            "Если аккаунт требует подтверждения, письмо отправлено.",
          );

        } catch (
          errorValue
        ) {
          error.innerHTML =
            `
            <div class="error">
              ${
                errorText(
                  errorValue,
                )
              }
            </div>
            `;

        } finally {
          button.disabled =
            false;
        }
      },
    );
}


async function runVerification(
  token,
) {
  const status =
    document.querySelector(
      "#verify-status",
    );

  const error =
    document.querySelector(
      "#verify-error",
    );


  try {
    await verifyEmail(
      token,
    );

    status.innerHTML =
      `
      <div class="notice">
        <span>✓</span>

        <p>
          <strong>
            Email подтверждён.
          </strong>
          <br>
          Теперь можно войти
          в аккаунт.
        </p>
      </div>
      `;

  } catch (
    errorValue
  ) {
    error.innerHTML =
      `
      <div class="error">
        ${
          errorText(
            errorValue,
          )
        }
      </div>
      `;
  }
}


// ============================================================
// FORGOT PASSWORD
// ============================================================


export function forgotPasswordPage() {
  authLayout(
    `
    <form
      class="auth-form"
      id="forgot-form"
    >

      <h1>
        Восстановление пароля
      </h1>

      <p class="subtitle">
        Укажите email аккаунта.
        Если он существует,
        Meditron отправит ссылку
        для смены пароля.
      </p>

      <div class="field">

        <label for="email">
          Email
        </label>

        <input
          id="email"
          name="email"
          type="email"
          required
          autocomplete="email"
          placeholder="you@example.com"
        >

      </div>

      <div
        id="forgot-error"
        role="alert"
      ></div>

      <button
        class="btn"
        type="submit"
      >
        Получить ссылку →
      </button>

      <p class="auth-switch">
        <a href="#/login">
          Вернуться ко входу
        </a>
      </p>

    </form>
    `,
  );


  document
    .querySelector(
      "#forgot-form",
    )
    .onsubmit =
      async (
        event,
      ) => {

        event.preventDefault();

        const form =
          event.currentTarget;

        const button =
          form.querySelector(
            "button[type=submit]",
          );

        const error =
          document.querySelector(
            "#forgot-error",
          );

        error.innerHTML =
          "";

        button.disabled =
          true;


        try {
          await forgotPassword(
            form.elements.namedItem(
              "email",
            ).value.trim(),
          );

          toast(
            "Если аккаунт существует, инструкция отправлена.",
          );

        } catch (
          errorValue
        ) {
          error.innerHTML =
            `
            <div class="error">
              ${
                errorText(
                  errorValue,
                )
              }
            </div>
            `;

        } finally {
          button.disabled =
            false;
        }
      };
}


// ============================================================
// RESET PASSWORD
// ============================================================


export function resetPasswordPage(
  params,
) {
  const token =
    params.get(
      "token",
    );


  authLayout(
    `
    <form
      class="auth-form"
      id="reset-form"
    >

      <h1>
        Новый пароль
      </h1>

      <p class="subtitle">
        Установите новый пароль
        для аккаунта.
      </p>

      ${
        !token
          ? `
            <div class="error">
              В ссылке отсутствует
              токен восстановления.
            </div>
          `
          : ""
      }

      <div class="field">

        <label for="password">
          Новый пароль
        </label>

        <input
          id="password"
          name="password"
          type="password"
          minlength="8"
          required
          autocomplete="new-password"
        >

      </div>

      <div class="field">

        <label for="repeat">
          Повторите пароль
        </label>

        <input
          id="repeat"
          name="repeat"
          type="password"
          minlength="8"
          required
          autocomplete="new-password"
        >

      </div>

      <div
        id="reset-error"
        role="alert"
      ></div>

      <button
        class="btn"
        type="submit"
        ${
          !token
            ? "disabled"
            : ""
        }
      >
        Изменить пароль →
      </button>

    </form>
    `,
  );


  document
    .querySelector(
      "#reset-form",
    )
    .onsubmit =
      async (
        event,
      ) => {

        event.preventDefault();

        if (
          !token
        ) {
          return;
        }

        const form =
          event.currentTarget;

        const password =
          form.elements.namedItem(
            "password",
          ).value;

        const repeat =
          form.elements.namedItem(
            "repeat",
          ).value;

        const button =
          form.querySelector(
            "button[type=submit]",
          );

        const error =
          document.querySelector(
            "#reset-error",
          );


        error.innerHTML =
          "";


        if (
          password !==
          repeat
        ) {
          error.innerHTML =
            `
            <div class="error">
              Пароли не совпадают.
            </div>
            `;

          return;
        }


        button.disabled =
          true;


        try {
          await resetPassword(
            token,
            password,
          );

          toast(
            "Пароль изменён. Войдите с новым паролем.",
          );

          location.hash =
            "/login";

        } catch (
          errorValue
        ) {
          error.innerHTML =
            `
            <div class="error">
              ${
                errorText(
                  errorValue,
                )
              }
            </div>
            `;

        } finally {
          button.disabled =
            false;
        }
      };
}

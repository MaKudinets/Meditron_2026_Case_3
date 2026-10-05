import { cfg } from "../config.js";

export { cfg };


const TOKEN_KEY =
  "meditron_access_token";


function readStoredToken() {
  try {
    return (
      globalThis.sessionStorage?.getItem(
        TOKEN_KEY,
      ) || null
    );
  } catch {
    return null;
  }
}


let token = readStoredToken();


export function getToken() {
  return token;
}


export function setToken(value) {
  token = value || null;

  try {
    if (token) {
      globalThis.sessionStorage?.setItem(
        TOKEN_KEY,
        token,
      );
    } else {
      globalThis.sessionStorage?.removeItem(
        TOKEN_KEY,
      );
    }
  } catch {
    // Если sessionStorage недоступен,
    // токен всё равно остаётся в памяти.
  }
}


export class ApiError extends Error {
  constructor(
    message,
    status = 0,
    details = null,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}


const messages = {
  400:
    "Проверьте отправленные данные.",

  401:
    "Сессия истекла. Войдите в аккаунт снова.",

  403:
    "Недостаточно прав для этого действия.",

  404:
    "Запрошенные данные не найдены.",

  409:
    "Эти данные уже используются.",

  413:
    "Файл слишком большой.",

  415:
    "Формат файла не поддерживается.",

  422:
    "Некоторые поля не соответствуют формату сервера.",

  429:
    "Слишком много запросов. Попробуйте позже.",

  500:
    "На сервере произошла ошибка.",

  502:
    "Сервис временно недоступен.",

  503:
    "Сервис временно недоступен.",
};


function makeUrl(path) {
  if (!cfg.apiUrl) {
    throw new ApiError(
      "Адрес API ещё не настроен.",
    );
  }

  const base =
    cfg.apiUrl.replace(/\/$/, "");

  return `${base}${path}`;
}


async function readErrorBody(
  response,
) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}


function extractFilename(
  response,
) {
  const disposition =
    response.headers.get(
      "Content-Disposition",
    );

  if (!disposition) {
    return null;
  }

  const utfMatch =
    disposition.match(
      /filename\*=UTF-8''([^;]+)/i,
    );

  if (utfMatch) {
    try {
      return decodeURIComponent(
        utfMatch[1],
      );
    } catch {
      return utfMatch[1];
    }
  }

  const match =
    disposition.match(
      /filename="?([^";]+)"?/i,
    );

  return match?.[1] || null;
}


export async function apiRequest(
  path,
  options = {},
) {
  const {
    responseType = "json",
    auth = true,
    ...fetchOptions
  } = options;

  const controller =
    new AbortController();

  const timer = setTimeout(
    () => controller.abort(),
    cfg.timeoutMs,
  );

  try {
    const headers =
      new Headers(
        fetchOptions.headers,
      );

    const body =
      fetchOptions.body;

    if (
      body &&
      !(body instanceof FormData) &&
      !headers.has("Content-Type")
    ) {
      headers.set(
        "Content-Type",
        "application/json",
      );
    }

    if (
      auth &&
      token
    ) {
      headers.set(
        "Authorization",
        `Bearer ${token}`,
      );
    }

    const response =
      await fetch(
        makeUrl(path),
        {
          ...fetchOptions,
          headers,
          signal:
            controller.signal,
        },
      );

    if (!response.ok) {
      const errorBody =
        await readErrorBody(
          response,
        );

      if (
        response.status === 401
      ) {
        setToken(null);
      }

      throw new ApiError(
        messages[
          response.status
        ] ||
          "Не удалось получить ответ сервера.",

        response.status,

        errorBody?.detail ??
          errorBody,
      );
    }

    if (
      response.status === 204
    ) {
      return null;
    }

    if (
      responseType === "blob"
    ) {
      return {
        blob:
          await response.blob(),

        filename:
          extractFilename(
            response,
          ),
      };
    }

    if (
      responseType === "text"
    ) {
      return response.text();
    }

    return await response
      .json()
      .catch(() => null);

  } catch (error) {
    if (
      error instanceof ApiError
    ) {
      throw error;
    }

    if (
      error?.name ===
      "AbortError"
    ) {
      throw new ApiError(
        "Сервер не ответил вовремя. Попробуйте ещё раз.",
      );
    }

    throw new ApiError(
      "Нет соединения с сервером. Проверьте подключение и повторите попытку.",
    );

  } finally {
    clearTimeout(
      timer,
    );
  }
}


export function apiBlob(
  path,
  options = {},
) {
  return apiRequest(
    path,
    {
      ...options,
      responseType:
        "blob",
    },
  );
}


export function health() {
  return apiRequest(
    cfg.endpoints.health,
    {
      auth: false,
    },
  );
}
import {
  apiRequest,
  cfg,
  setToken,
  getToken,
  ApiError,
} from "./client.js";

import {
  delay,
} from "../mocks/screening.js";


export let currentUser = null;


// ============================================================
// CURRENT USER STATE
// ============================================================


export function setCurrentUser(
  user,
) {
  currentUser =
    user || null;

  return currentUser;
}


// ============================================================
// RESTORE SESSION
// ============================================================


export async function restoreSession() {
  if (
    cfg.mode === "demo"
  ) {
    return null;
  }

  if (
    !getToken()
  ) {
    currentUser = null;
    return null;
  }

  try {
    currentUser =
      await apiRequest(
        cfg.endpoints.me,
      );

    return currentUser;

  } catch (error) {
    setToken(null);
    currentUser = null;

    if (
      error?.status === 401
    ) {
      return null;
    }

    throw error;
  }
}


// ============================================================
// LOGIN
// ============================================================


export async function login(
  data,
) {
  if (
    cfg.mode === "demo"
  ) {
    await delay();

    currentUser = {
      id: "demo",
      email:
        data.email,
      role: "patient",
      is_email_verified: true,
    };

    return currentUser;
  }

  const response =
    await apiRequest(
      cfg.endpoints.login,
      {
        method: "POST",

        auth: false,

        body:
          JSON.stringify({
            email:
              data.email,

            password:
              data.password,
          }),
      },
    );

  if (
    !response?.access_token
  ) {
    throw new ApiError(
      "Сервер не вернул токен авторизации.",
    );
  }

  setToken(
    response.access_token,
  );

  if (
    response.user
  ) {
    currentUser =
      response.user;

    return currentUser;
  }

  try {
    currentUser =
      await apiRequest(
        cfg.endpoints.me,
      );

    return currentUser;

  } catch (error) {
    setToken(null);
    currentUser = null;

    throw error;
  }
}


// ============================================================
// REGISTER
// ============================================================


export async function register(
  data,
) {
  if (
    cfg.mode === "demo"
  ) {
    await delay();

    return {
      user: {
        id: "demo",
        email:
          data.email,
        role:
          data.role ||
          "patient",
        is_email_verified:
          false,
      },

      message:
        "Demo registration",

      email_sent:
        true,
    };
  }

  return apiRequest(
    cfg.endpoints.register,
    {
      method: "POST",

      auth: false,

      body:
        JSON.stringify({
          email:
            data.email,

          password:
            data.password,

          role:
            data.role,
        }),
    },
  );
}


// ============================================================
// VERIFY EMAIL
// ============================================================


export async function verifyEmail(
  token,
) {
  return apiRequest(
    cfg.endpoints.verifyEmail,
    {
      method: "POST",

      auth: false,

      body:
        JSON.stringify({
          token,
        }),
    },
  );
}


// ============================================================
// RESEND VERIFICATION
// ============================================================


export async function resendVerification(
  email,
) {
  return apiRequest(
    cfg.endpoints.resendVerification,
    {
      method: "POST",

      auth: false,

      body:
        JSON.stringify({
          email,
        }),
    },
  );
}


// ============================================================
// FORGOT PASSWORD
// ============================================================


export async function forgotPassword(
  email,
) {
  return apiRequest(
    cfg.endpoints.forgotPassword,
    {
      method: "POST",

      auth: false,

      body:
        JSON.stringify({
          email,
        }),
    },
  );
}


// ============================================================
// RESET PASSWORD
// ============================================================


export async function resetPassword(
  token,
  newPassword,
) {
  return apiRequest(
    cfg.endpoints.resetPassword,
    {
      method: "POST",

      auth: false,

      body:
        JSON.stringify({
          token,

          new_password:
            newPassword,
        }),
    },
  );
}


// ============================================================
// LOGOUT
// ============================================================


export async function logout() {
  if (
    cfg.mode !== "demo" &&
    getToken()
  ) {
    try {
      await apiRequest(
        cfg.endpoints.logout,
        {
          method: "POST",
        },
      );
    } catch {
      // Даже если сервер недоступен,
      // локальную сессию очищаем.
    }
  }

  setToken(null);
  currentUser = null;
}
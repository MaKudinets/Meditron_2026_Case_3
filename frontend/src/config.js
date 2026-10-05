const env = import.meta.env || {};

export const cfg = globalThis.MEDITRON_CONFIG || {
  mode:
    env.VITE_USE_MOCKS === "false"
      ? "live"
      : "demo",

  apiUrl:
    env.VITE_API_URL ||
    "http://127.0.0.1:8000",

  // Временно оставляем до переделки
  // старого screening.js.
  requestFormat:
    env.VITE_REQUEST_FORMAT ||
    "features",

  timeoutMs: 30000,

  endpoints: {
    // ----------------------------------------
    // System
    // ----------------------------------------

    health:
      "/health",

    metaFeatures:
      "/api/v1/meta/features",

    metaModel:
      "/api/v1/meta/model",

    // ----------------------------------------
    // Auth
    // ----------------------------------------

    register:
      "/api/v1/auth/register",

    verifyEmail:
      "/api/v1/auth/verify-email",

    resendVerification:
      "/api/v1/auth/resend-verification",

    login:
      "/api/v1/auth/login",

    me:
      "/api/v1/auth/me",

    logout:
      "/api/v1/auth/logout",

    forgotPassword:
      "/api/v1/auth/forgot-password",

    resetPassword:
      "/api/v1/auth/reset-password",

    // ----------------------------------------
    // Patient
    // ----------------------------------------

    screenings:
      "/api/v1/me/screenings",

    history:
      "/api/v1/me/screenings",

    patientImport:
      "/api/v1/me/imports/lab-file",

    trends:
      "/api/v1/me/trends",

    // ----------------------------------------
    // Doctor
    // ----------------------------------------

    doctorImport:
      "/api/v1/doctor/imports/lab-file",

    doctorBulkScreening:
      "/api/v1/doctor/screenings/bulk",

    doctorPatients:
      "/api/v1/doctor/patients",
  },
};
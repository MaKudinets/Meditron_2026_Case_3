import "./styles.css";

import {
  normalizeAuthLinks,
  route,
} from "./router.js";

import {
  restoreSession,
} from "./api/auth.js";


// ============================================================
// APP START
// ============================================================


async function start() {
  normalizeAuthLinks();

  try {
    await restoreSession();
  } catch (
    error
  ) {
    console.error(
      "Session restore failed:",
      error,
    );
  }

  await route();
}


start();
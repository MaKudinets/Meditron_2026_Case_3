import assert from "node:assert/strict";
import { JSDOM } from "jsdom";
const dom = new JSDOM(
  '<header id="header"></header><main></main><footer id="footer"></footer><div id="toast"></div>',
  { url: "http://localhost:5173/" },
);
for (const key of ["window", "document", "location", "FormData"])
  globalThis[key] = dom.window[key];
globalThis.MEDITRON_CONFIG = {
  mode: "demo",
  apiUrl: "",
  requestFormat: "labs",
  timeoutMs: 100,
  endpoints: { screenings: "/api/v1/screenings", batch: null },
};
const { screening } = await import("../src/pages/screening.js");
const { results } = await import("../src/pages/results.js");
const { historyPage } = await import("../src/pages/historyPage.js");
const { trendsPage } = await import("../src/pages/trendsPage.js");
const { auth } = await import("../src/pages/auth.js");
const { parseCSV } = await import("../src/components/index.js");
const { state } = await import("../src/state.js");
const submit = { preventDefault() {} };
screening();
let form = document.querySelector("#screening-form");
await form.onsubmit(submit);
assert.match(document.querySelector("#form-error").textContent, /хотя бы один/);
form.elements.namedItem("ferritin").value = "16,5";
form.elements.namedItem("consent").checked = true;
await form.onsubmit(submit);
assert.equal(location.hash, "#/result");
assert.deepEqual(state.result.labs, [
  { code: "ferritin", value: 16.5, unit: "ng/ml" },
]);
results();
assert.match(
  document.querySelector("main").textContent,
  /Демонстрационные данные/,
);
await historyPage();
assert.equal(document.querySelectorAll("[data-open]").length, 4);
await trendsPage();
assert.ok(document.querySelectorAll("svg.chart").length >= 3);
auth(true);
form = document.querySelector("#auth-form");
form.elements.namedItem("email").value = "test@example.org";
form.elements.namedItem("password").value = "12345678";
form.elements.namedItem("repeat").value = "otherpassword";
await form.onsubmit({ ...submit, currentTarget: form });
assert.match(document.querySelector("#auth-error").textContent, /не совпадают/);
assert.deepEqual(parseCSV('patient_id;notes\nP001;"text;with delimiter"'), [
  ["patient_id", "notes"],
  ["P001", "text;with delimiter"],
]);
assert.throws(() => parseCSV('patient_id,notes\nP001,"bad'), /кавычку/);
console.log(
  "UI flow passed: empty form, decimal comma, omission handling, result, history, charts, password confirmation and quoted CSV.",
);
dom.window.close();

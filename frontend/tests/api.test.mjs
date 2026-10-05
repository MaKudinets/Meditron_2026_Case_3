import assert from "node:assert/strict";
globalThis.MEDITRON_CONFIG = {
  mode: "live",
  apiUrl: "https://api.example.org",
  requestFormat: "labs",
  timeoutMs: 10,
  endpoints: { screenings: "/api/v1/screenings" },
};
const { makePayload, validateResult } = await import("../src/api/screening.js");
const { apiRequest, setToken, ApiError } = await import("../src/api/client.js");
const form = {
  age: null,
  sex: "",
  symptoms: " ",
  labs: [
    { code: "ferritin", value: null, unit: "ng/ml" },
    { code: "hemoglobin", value: 0, unit: "g/l" },
  ],
};
assert.deepEqual(makePayload(form), {
  labs: [{ code: "hemoglobin", value: 0, unit: "g/l" }],
});
assert.throws(() => makePayload({ ...form, labs: [] }), /хотя бы/);
assert.throws(
  () => makePayload({ ...form, labs: [{ code: "ferritin", value: NaN }] }),
  /числами/,
);
MEDITRON_CONFIG.requestFormat = "features";
assert.deepEqual(makePayload(form), { features: { hemoglobin: 0 } });
assert.throws(
  () => validateResult({ predicted_class: "x", confidence: 2 }),
  ApiError,
);
assert.throws(
  () =>
    validateResult({
      predicted_class: "x",
      confidence: 0.5,
      probabilities: { x: "0.5" },
    }),
  ApiError,
);
assert.throws(
  () =>
    validateResult({
      predicted_class: "x",
      confidence: 0.5,
      top_features: [{ feature: "x", importance: null }],
    }),
  ApiError,
);
assert.equal(
  validateResult({ predicted_class: "unknown", confidence: 0.6 })
    .predicted_class,
  "unknown",
);
setToken("test-token");
globalThis.fetch = async (url, opts) => {
  assert.equal(url, "https://api.example.org/test");
  assert.equal(opts.headers.get("Authorization"), "Bearer test-token");
  return new Response(JSON.stringify({ status: "ok" }));
};
assert.deepEqual(await apiRequest("/test"), { status: "ok" });
globalThis.fetch = async () =>
  new Response(
    JSON.stringify({ detail: [{ loc: ["body", "labs"], msg: "invalid" }] }),
    { status: 422 },
  );
await assert.rejects(
  apiRequest("/test"),
  (e) => e.status === 422 && Array.isArray(e.details),
);
globalThis.fetch = async () => {
  throw new TypeError("network");
};
await assert.rejects(apiRequest("/test"), /Нет соединения/);
globalThis.fetch = async (url, opts) =>
  new Promise((resolve, reject) =>
    opts.signal.addEventListener("abort", () =>
      reject(new DOMException("Timeout", "AbortError")),
    ),
  );
await assert.rejects(apiRequest("/test"), /вовремя/);
console.log(
  "API checks passed: omissions, zero values, request formats, response validation, Bearer, HTTP 422, network failure, timeout.",
);

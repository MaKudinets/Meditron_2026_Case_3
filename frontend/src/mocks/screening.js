export const fixture = {
  predicted_class: "iron_deficiency",
  confidence: 0.87,
  probabilities: {
    iron_deficiency: 0.87,
    vitamin_d_deficiency: 0.21,
    b12_deficiency: 0.08,
  },
  top_features: [
    { feature: "ferritin", importance: 0.64 },
    { feature: "hemoglobin", importance: 0.21 },
  ],
  quality_warnings: [
    "Демонстрационный ответ. Значения не вычислены по вашим анализам.",
  ],
  model_version: "demo",
};
export let history = [
  {
    id: "demo-3",
    created_at: "2026-10-04T09:00:00Z",
    labs: [
      { code: "ferritin", value: 26, unit: "ng/ml" },
      { code: "vitamin_d", value: 29, unit: "ng/ml" },
      { code: "hemoglobin", value: 132, unit: "g/l" },
    ],
    result: { ...fixture, confidence: 0.67 },
  },
  {
    id: "demo-2",
    created_at: "2026-09-01T09:00:00Z",
    labs: [
      { code: "ferritin", value: 19, unit: "ng/ml" },
      { code: "vitamin_d", value: 24, unit: "ng/ml" },
      { code: "hemoglobin", value: 128, unit: "g/l" },
    ],
    result: { ...fixture, confidence: 0.76 },
  },
  {
    id: "demo-1",
    created_at: "2026-08-01T09:00:00Z",
    labs: [
      { code: "ferritin", value: 12, unit: "ng/ml" },
      { code: "vitamin_d", value: 21, unit: "ng/ml" },
      { code: "hemoglobin", value: 124, unit: "g/l" },
    ],
    result: fixture,
  },
];
export function addHistory(item) {
  history.unshift(item);
}
export function clearHistory() {
  history.length = 0;
}
export const delay = () => new Promise((resolve) => setTimeout(resolve, 650));

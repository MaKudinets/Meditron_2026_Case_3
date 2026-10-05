export type LabValue = { code: string; value: number | null; unit: string };
export interface ScreeningForm {
  age: number | null;
  sex: "" | "male" | "female";
  symptoms?: string;
  labs: LabValue[];
}
export interface ScreeningResult {
  predicted_class: string;
  confidence: number;
  probabilities?: Record<string, number>;
  top_features?: { feature: string; importance: number }[];
  quality_warnings?: string[];
  model_version?: string;
}
export interface ScreeningRecord {
  id?: string;
  created_at: string;
  labs: LabValue[];
  result: ScreeningResult;
}
export interface User {
  id: string | number;
  email: string;
  role?: "patient" | "doctor";
}
export interface LabTrend {
  code: string;
  unit: string;
  points: { date: string; value: number }[];
  reference_low?: number;
  reference_high?: number;
  reference_source?: string;
}

import createClient from "openapi-fetch";
import type { paths, components } from "./api-types";

export type Schemas = components["schemas"];
export type EmbedResponse = Schemas["EmbedResponse"];
export type ExtractResponse = Schemas["ExtractResponse"];
export type DistortionMetrics = Schemas["DistortionMetrics"];
export type ExperimentStartResponse = Schemas["ExperimentStartResponse"];
export type HistoryResponse = Schemas["HistoryResponse"];
export type OperationItemResponse = Schemas["OperationItemResponse"];
export type HistoryClearResponse = Schemas["HistoryClearResponse"];
export type HealthResponse = Schemas["HealthResponse"];

export interface PoVBin {
  k: number;
  even_val: number;
  odd_val: number;
  even_count: number;
  odd_count: number;
  diff: number;
}

export interface PoVHistogramData {
  channel: string;
  total_samples: number;
  bins: PoVBin[];
}

export interface ChiSquareData {
  chi2: number;
  p_value: number;
  df: number;
  classification: string;
  details?: Record<string, unknown>;
}

export interface RSAnalysisData {
  estimated_payload_ratio: number;
  regular_m: number;
  singular_m: number;
  regular_neg_m: number;
  singular_neg_m: number;
  classification: string;
  channel_ratios?: Record<string, number>;
}

export interface AnalyzeResponse {
  operation_id: string;
  mse: number;
  psnr: number;
  ssim: number;
  heatmap_url: string;
  bitplane_url: string;
  pov_histogram: PoVHistogramData;
}

export interface DetectResponse {
  operation_id: string;
  chi_square: ChiSquareData;
  rs_analysis: RSAnalysisData;
  classification: string;
}

const BASE_URL =
  typeof window !== "undefined"
    ? (process.env.NEXT_PUBLIC_BACKEND_URL || "")
    : (process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000");

export const apiClient = createClient<paths>({
  baseUrl: BASE_URL,
  credentials: "include",
});

/**
 * Robust API helper functions for StegaShield services with explicit error unwrapping
 */

export async function embedPayload(formData: FormData): Promise<EmbedResponse> {
  const url = `${BASE_URL}/api/v1/stego/embed`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({ detail: res.statusText }))) as {
      detail?: string | Array<{ msg?: string }>;
    };
    const msg =
      typeof errorData.detail === "string"
        ? errorData.detail
        : Array.isArray(errorData.detail) && errorData.detail[0]?.msg
        ? errorData.detail[0].msg
        : `Embedding failed with status ${res.status}`;
    throw new Error(msg);
  }

  return res.json() as Promise<EmbedResponse>;
}

export async function extractPayload(formData: FormData): Promise<ExtractResponse> {
  const url = `${BASE_URL}/api/v1/stego/extract`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({ detail: res.statusText }))) as {
      detail?: string;
    };
    const msg =
      typeof errorData.detail === "string"
        ? errorData.detail
        : "Extraction failed: wrong password or no payload found.";
    throw new Error(msg);
  }

  return res.json() as Promise<ExtractResponse>;
}

export async function analyzeComparison(formData: FormData): Promise<AnalyzeResponse> {
  const url = `${BASE_URL}/api/v1/stego/analyze`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({ detail: res.statusText }))) as {
      detail?: string;
    };
    const msg = typeof errorData.detail === "string" ? errorData.detail : "Image analysis failed";
    throw new Error(msg);
  }

  return res.json() as Promise<AnalyzeResponse>;
}

export async function detectSteganography(formData: FormData): Promise<DetectResponse> {
  const url = `${BASE_URL}/api/v1/stego/detect`;
  const res = await fetch(url, {
    method: "POST",
    body: formData,
    credentials: "include",
  });

  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({ detail: res.statusText }))) as {
      detail?: string;
    };
    const msg =
      typeof errorData.detail === "string" ? errorData.detail : "Steganalysis detection failed";
    throw new Error(msg);
  }

  return res.json() as Promise<DetectResponse>;
}

export async function startAttackLab(config: {
  methods: string[];
  ratios: number[];
  detectors: string[];
}): Promise<ExperimentStartResponse> {
  const url = `${BASE_URL}/api/v1/attack-lab/run`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config),
    credentials: "include",
  });

  if (res.status === 409) {
    throw new Error(
      "ACTIVE_EXPERIMENT_RUNNING: Another Attack Lab experiment is currently in progress. Please wait for it to complete."
    );
  }

  if (!res.ok) {
    const errorData = (await res.json().catch(() => ({ detail: res.statusText }))) as {
      detail?: string;
    };
    const msg =
      typeof errorData.detail === "string" ? errorData.detail : "Failed to start experiment";
    throw new Error(msg);
  }

  return res.json() as Promise<ExperimentStartResponse>;
}

export async function fetchHistory(): Promise<HistoryResponse> {
  const url = `${BASE_URL}/api/v1/history`;
  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`Failed to load history: ${res.statusText}`);
  }

  return res.json() as Promise<HistoryResponse>;
}

export async function clearHistory(): Promise<HistoryClearResponse> {
  const url = `${BASE_URL}/api/v1/history`;
  const res = await fetch(url, {
    method: "DELETE",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`Failed to clear history: ${res.statusText}`);
  }

  return res.json() as Promise<HistoryClearResponse>;
}

export async function checkHealth(): Promise<HealthResponse> {
  const url = `${BASE_URL}/api/v1/health`;
  const res = await fetch(url, {
    method: "GET",
    credentials: "include",
  });

  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }

  return res.json() as Promise<HealthResponse>;
}

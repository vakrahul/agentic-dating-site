import type {
  ExportData,
  PersonDetailOut,
  PersonOut,
  PairOut,
  RankingsOverview,
  RankingOut,
  RunOut,
} from "./types";

export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000"
).replace(/\/$/, "");

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (Array.isArray(body?.detail)) detail = body.detail.map((d: { msg?: string }) => d.msg || JSON.stringify(d)).join("; ");
    } catch {
      /* keep status text */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  createPeople: (rows: { linkedin_url: string; instagram_url: string; name?: string }[]) =>
    request<{ created: PersonOut[]; errors: { index: number; message: string }[]; count: number }>(
      "/api/people",
      { method: "POST", body: JSON.stringify({ people: rows }) }
    ),
  listPeople: () => request<PersonOut[]>("/api/people"),
  getPerson: (id: number | string) => request<PersonDetailOut>(`/api/people/${id}`),
  startRun: () => request<RunOut>("/api/run", { method: "POST" }),
  getRun: () => request<RunOut | null>("/api/run"),
  getPair: (a: number | string, b: number | string) => request<PairOut[]>(`/api/pair/${a}/${b}`),
  regeneratePair: (a: number | string, b: number | string, round: number = 1) =>
    request<PairOut>(`/api/pair/${a}/${b}/regenerate?round=${round}`, { method: "POST" }),
  rankingsOverview: () => request<RankingsOverview>("/api/rankings"),
  getRanking: (id: number | string) => request<RankingOut>(`/api/rankings/${id}`),
  exportRun: () => request<ExportData>("/api/export"),
  importRun: (data: ExportData) =>
    request<{ imported: Record<string, number>; idempotent: boolean }>("/api/import", {
      method: "POST",
      body: JSON.stringify({ data }),
    }),
  processQueue: (includeFailed = false) =>
    request<{ resumed_count: number; person_ids: number[] }>(
      `/api/people/process-queue?include_failed=${includeFailed}`,
      { method: "POST" }
    ),
  retryPerson: (id: number | string) =>
    request<{ ok: boolean; person_id: number }>(`/api/people/${id}/retry`, {
      method: "POST",
    }),
};

export function openEventStream(onEvent: (event: unknown) => void): () => void {
  const source = new EventSource(`${API_BASE}/api/run/stream`);
  source.onmessage = (message) => {
    try {
      onEvent(JSON.parse(message.data));
    } catch {
      /* ignore malformed frame */
    }
  };
  return () => source.close();
}

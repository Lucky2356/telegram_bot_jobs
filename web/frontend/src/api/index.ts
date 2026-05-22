import type {
  VacancyFilter, FilterFormData, AppConfig, ResultsResponse, HistoryResponse, Stats,
} from '../types'

const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(text || `HTTP ${resp.status}`)
  }
  return resp.json()
}

export const api = {
  getConfig: (): Promise<AppConfig> => request(`${BASE}/config`),

  getFilters: (): Promise<VacancyFilter[]> => request(`${BASE}/filters`),

  createFilter: (data: FilterFormData): Promise<{ ok: boolean; filter: VacancyFilter }> =>
    request(`${BASE}/filters`, { method: 'POST', body: JSON.stringify(data) }),

  updateFilter: (id: number, data: FilterFormData): Promise<{ ok: boolean; filter: VacancyFilter }> =>
    request(`${BASE}/filters/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteFilter: (id: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/filters/${id}`, { method: 'DELETE' }),

  toggleFilter: (id: number): Promise<{ ok: boolean; active: boolean }> =>
    request(`${BASE}/filters/${id}/toggle`, { method: 'POST' }),

  getHistory: (page = 1, limit = 20): Promise<HistoryResponse> =>
    request(`${BASE}/history?page=${page}&limit=${limit}`),

  getStats: (): Promise<Stats> => request(`${BASE}/stats`),

  checkNow: (): Promise<{ ok: boolean; message: string }> =>
    request(`${BASE}/check_now`, { method: 'POST' }),

  getResults: (): Promise<ResultsResponse> => request(`${BASE}/results`),
}

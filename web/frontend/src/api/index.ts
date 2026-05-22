import type { VacancyFilter, HistoryItem, Stats, FilterFormData, AppConfig, VacancyResult } from '../types'

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

  getFilter: (id: number): Promise<VacancyFilter> => request(`${BASE}/filters/${id}`),

  createFilter: (data: FilterFormData): Promise<{ ok: boolean; filter: VacancyFilter }> =>
    request(`${BASE}/filters`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateFilter: (id: number, data: FilterFormData): Promise<{ ok: boolean; filter: VacancyFilter }> =>
    request(`${BASE}/filters/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteFilter: (id: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/filters/${id}`, { method: 'DELETE' }),

  toggleFilter: (id: number): Promise<{ ok: boolean; active: boolean }> =>
    request(`${BASE}/filters/${id}/toggle`, { method: 'POST' }),

  getHistory: (): Promise<HistoryItem[]> => request(`${BASE}/history`),

  getStats: (): Promise<Stats> => request(`${BASE}/stats`),

  checkNow: (): Promise<{ ok: boolean; message: string }> =>
    request(`${BASE}/check_now`, { method: 'POST' }),

  getResults: (): Promise<{ items: VacancyResult[]; checked_at: string | null }> =>
    request(`${BASE}/results`),
}

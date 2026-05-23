import type {
  VacancyFilter, FilterFormData, AppConfig, ResultsResponse, HistoryResponse, Stats,
  SavedVacancy, BlocklistItem, ParserStatus,
} from '../types'

const BASE = '/api'

function getAuthHeaders(): Record<string, string> {
  const token = sessionStorage.getItem('auth_token')
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const resp = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...getAuthHeaders(), ...options?.headers },
  })
  if (resp.status === 401) {
    sessionStorage.removeItem('auth_token')
    window.location.reload()
    return undefined as T
  }
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

  cloneFilter: (id: number): Promise<{ ok: boolean; filter: VacancyFilter }> =>
    request(`${BASE}/filters/${id}/clone`, { method: 'POST' }),

  toggleFilter: (id: number): Promise<{ ok: boolean; active: boolean }> =>
    request(`${BASE}/filters/${id}/toggle`, { method: 'POST' }),

  checkFilter: (id: number): Promise<{ ok: boolean; message: string }> =>
    request(`${BASE}/filters/${id}/check`, { method: 'POST' }),

  getHistory: (page = 1, limit = 20): Promise<HistoryResponse> =>
    request(`${BASE}/history?page=${page}&limit=${limit}`),

  getStats: (): Promise<Stats> => request(`${BASE}/stats`),

  checkNow: (): Promise<{ ok: boolean; message: string }> =>
    request(`${BASE}/check_now`, { method: 'POST' }),

  getResults: (): Promise<ResultsResponse> => request(`${BASE}/results`),

  getSaved: (): Promise<SavedVacancy[]> => request(`${BASE}/saved`),

  getBlocklist: (): Promise<BlocklistItem[]> => request(`${BASE}/blocklist`),

  deleteBlocklist: (id: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/blocklist/${id}/delete`, { method: 'POST' }),

  getStatus: (): Promise<ParserStatus> => request(`${BASE}/status`),

  saveVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/save`, { method: 'POST' }),

  unsaveVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/unsave`, { method: 'POST' }),

  blockVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/block`, { method: 'POST' }),

  deleteSaved: (savedId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/saved/${savedId}`, { method: 'DELETE' }),

  addBlocklist: (pattern: string, type: string = 'company'): Promise<{ ok: boolean }> =>
    request(`${BASE}/blocklist/add`, { method: 'POST', body: JSON.stringify({ pattern, type }) }),
}

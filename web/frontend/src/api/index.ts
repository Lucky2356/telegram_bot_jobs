import type {
  VacancyFilter, FilterFormData, AppConfig, ResultsResponse, HistoryResponse, Stats,
  SavedVacancy, BlocklistItem, ParserStatus,
  FilterDiagnostics, ParserHealthItem, EventLogItem,
  BackupItem, BackupResponse, DeliveryItem, DeliveryStatus, FilterPerformanceItem,
  ConfigDiagnostics, FilterRecommendation,
  TaskStatus,
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

  logout: (): Promise<{ ok: boolean }> => request(`${BASE}/auth/logout`, { method: 'POST' }),

  getConfigDiagnostics: (): Promise<ConfigDiagnostics> => request(`${BASE}/config/diagnostics`),

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

  previewFilter: (id: number): Promise<ResultsResponse> =>
    request(`${BASE}/filters/${id}/preview`, { method: 'POST' }),

  diagnoseFilter: (id: number): Promise<FilterDiagnostics> =>
    request(`${BASE}/filters/${id}/diagnostics`),

  getFilterRecommendations: (id: number): Promise<{ filter_id: number; recommendations: FilterRecommendation[] }> =>
    request(`${BASE}/filters/${id}/recommendations`),

  exportFilters: (): Promise<{ version: number; filters: FilterFormData[] }> =>
    request(`${BASE}/filters/export`),

  importFilters: (filters: FilterFormData[], replace = false): Promise<{ ok: boolean; created: VacancyFilter[] }> =>
    request(`${BASE}/filters/import`, { method: 'POST', body: JSON.stringify({ filters, replace }) }),

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

  getParserHealth: (): Promise<ParserHealthItem[]> => request(`${BASE}/parsers/health`),

  getParserHealthHistory: (): Promise<ParserHealthItem[]> => request(`${BASE}/sources/health-history`),

  getEventLogs: (): Promise<EventLogItem[]> => request(`${BASE}/events/logs`),

  getTaskStatus: (): Promise<TaskStatus> => request(`${BASE}/tasks/status`),

  getDeliveryStatus: (): Promise<DeliveryStatus> => request(`${BASE}/delivery/status`),

  getRecentDeliveries: (): Promise<DeliveryItem[]> => request(`${BASE}/delivery/recent`),

  retryDelivery: (): Promise<DeliveryStatus & { restored: number }> =>
    request(`${BASE}/delivery/retry`, { method: 'POST' }),

  cleanupDelivery: (): Promise<DeliveryStatus & { ok: boolean; deleted: number }> =>
    request(`${BASE}/delivery/cleanup`, { method: 'POST' }),

  getFilterPerformance: (): Promise<FilterPerformanceItem[]> => request(`${BASE}/filters/performance`),

  createBackup: (): Promise<BackupResponse> =>
    request(`${BASE}/backup`, { method: 'POST' }),

  exportBackup: (): Promise<unknown> => request(`${BASE}/backup/export`),

  listBackups: (): Promise<BackupItem[]> => request(`${BASE}/backup/list`),

  saveVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/save`, { method: 'POST' }),

  unsaveVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/unsave`, { method: 'POST' }),

  blockVacancy: (vacancyId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/vacancies/${vacancyId}/block`, { method: 'POST' }),

  reportBadVacancy: (
    vacancyId: number,
    filterId?: number | null,
    action = 'exclude_noise',
  ): Promise<{ ok: boolean; applied: string[]; suggestions: string[] }> =>
    request(`${BASE}/vacancies/${vacancyId}/feedback`, {
      method: 'POST',
      body: JSON.stringify({ filter_id: filterId ?? null, action }),
    }),

  deleteSaved: (savedId: number): Promise<{ ok: boolean }> =>
    request(`${BASE}/saved/${savedId}`, { method: 'DELETE' }),

  addBlocklist: (pattern: string, type: string = 'company'): Promise<{ ok: boolean }> =>
    request(`${BASE}/blocklist/add`, { method: 'POST', body: JSON.stringify({ pattern, type }) }),
}

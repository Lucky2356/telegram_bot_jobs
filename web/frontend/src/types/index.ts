export interface VacancyFilter {
  id: number; name: string; keywords: string[]
  city: string | null; salary_min: number | null; salary_max: number | null
  employment_types: string[]; sites: string[]
  exclude_keywords: string[]; experience: string | null; active: boolean
}

export interface HistoryItem {
  vacancy_title: string; company: string | null; salary: string | null
  source: string; url: string; filter_name: string | null; sent_at: string
}

export interface Stats {
  total_filters: number; active_filters: number
  total_vacancies: number; total_sent: number
  sent_by_source: Record<string, number>
  sent_by_day: { date: string; count: number }[]
  sent_last_7d: number; sent_last_30d: number
}

export interface FilterFormData {
  name: string; keywords: string[]; city: string | null
  salary_min: number | null; salary_max: number | null
  employment_types: string[]; sites: string[]
  exclude_keywords: string[]; experience: string | null
}

export interface AppConfig {
  employment_types: Record<string, string>; sites: Record<string, string>
  cities: Record<string, string>; experiences: Record<string, string>
  salaries: [string, string, number | null, number | null][]
  keyword_groups: Record<string, Record<string, string[]>>
}

export interface VacancyResult {
  id: number; filter_id?: number | null; filter_name?: string | null
  title: string; company: string | null; salary_text: string | null
  city: string | null; employment_type: string | null
  experience: string | null; description: string | null
  url: string; source: string; published_at: string | null
  score?: number
}

export interface ResultsResponse {
  items: VacancyResult[]; checked_at: string | null; checking: boolean
}

export interface HistoryResponse {
  items: HistoryItem[]; page: number; has_more: boolean
}

export interface SavedVacancy {
  id: number; vacancy_title: string; company: string | null
  salary_text: string | null; city: string | null
  employment_type: string | null; description: string | null
  url: string; source: string; published_at: string | null; saved_at: string
}

export interface BlocklistItem {
  id: number; pattern: string; type: string
}

export interface ParserStatus {
  hh: boolean; superjob: boolean; trudvsem: boolean
  rabota: boolean; habr: boolean
}

export type SalaryTuple = [string, string, number | null, number | null]

export interface DiagnosticSite {
  site: string
  raw: number
  passed: number
  rejected: Record<string, number>
  samples: { title: string; company: string | null; source: string; city: string | null; score: number }[]
  error?: string
}

export interface FilterDiagnostics {
  ok: boolean
  filter_id: number
  filter_name: string
  queries: string[]
  sites: DiagnosticSite[]
}

export interface ParserHealthItem {
  site: string
  ok: boolean
  count: number
  latency_ms?: number
  error?: string
  checked_at?: string
  cached?: boolean
}

export interface EventLogItem {
  ts: number
  type: string
  [key: string]: unknown
}

export interface DeliveryStatus {
  pending: number
  sent: number
  failed: number
}

export interface DeliveryItem {
  id: number
  chat_id: number
  vacancy_id: number | null
  source: string
  url: string
  status: string
  attempts: number
  last_error: string | null
  created_at: string | null
  updated_at: string | null
}

export interface FilterPerformanceItem {
  filter_id: number
  filter_name: string
  sent_count: number
  last_sent_at: string | null
}

export interface BackupResponse {
  ok: boolean
  file: string
  size: number
}

export interface BackupItem {
  file: string
  name: string
  size: number
  modified_at: string
}

export interface ConfigWarning {
  level: string
  message: string
}

export interface ConfigDiagnostics {
  warnings: ConfigWarning[]
  auth_enabled: boolean
  cors_origins: string[]
  database: string
  search_cache_seconds: number
}

export interface TaskStatus {
  queued: number
  worker_running: boolean
  checking: boolean
}

export interface FilterRecommendation {
  type: string
  message: string
}

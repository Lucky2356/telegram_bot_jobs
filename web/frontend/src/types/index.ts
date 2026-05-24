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

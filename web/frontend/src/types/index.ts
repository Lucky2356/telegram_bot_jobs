export interface VacancyFilter {
  id: number
  name: string
  keywords: string[]
  city: string | null
  salary_min: number | null
  salary_max: number | null
  employment_types: string[]
  sites: string[]
  exclude_keywords: string[]
  experience: string | null
  active: boolean
}

export interface HistoryItem {
  vacancy_title: string
  company: string | null
  salary: string | null
  source: string
  url: string
  filter_name: string | null
  sent_at: string
}

export interface Stats {
  total_filters: number
  active_filters: number
  total_vacancies: number
  total_sent: number
  sent_by_source: Record<string, number>
  sent_by_day: { date: string; count: number }[]
  sent_last_7d: number
  sent_last_30d: number
}

export interface FilterFormData {
  name: string
  keywords: string[]
  city: string | null
  salary_min: number | null
  salary_max: number | null
  employment_types: string[]
  sites: string[]
  exclude_keywords: string[]
  experience: string | null
}

export interface AppConfig {
  employment_types: Record<string, string>
  sites: Record<string, string>
  cities: Record<string, string>
  experiences: Record<string, string>
  salaries: [string, string, number | null, number | null][]
  keyword_groups: Record<string, Record<string, string[]>>
}

export type SalaryTuple = [string, string, number | null, number | null]

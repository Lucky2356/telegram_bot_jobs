import type { VacancyResult, AppConfig } from '../types'

interface VacancyCardProps {
  vacancy: VacancyResult
  config: AppConfig
}

const sourceColors: Record<string, string> = {
  hh: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300',
  superjob: 'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300',
  trudvsem: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300',
  rabota: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  habr: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300',
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России',
  rabota: 'rabota.ru', habr: 'Хабр Карьера',
}

export default function VacancyCard({ vacancy, config }: VacancyCardProps) {
  const handleKeyDown = (e: React.KeyboardEvent, url: string) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  const empLabel = vacancy.employment_type
    ? config.employment_types[vacancy.employment_type] || vacancy.employment_type
    : null

  const timeAgo = vacancy.published_at
    ? (() => {
        const diff = Date.now() - new Date(vacancy.published_at).getTime()
        const hours = Math.floor(diff / 3600000)
        if (hours < 1) return 'только что'
        if (hours < 24) return `${hours} ч. назад`
        const days = Math.floor(hours / 24)
        if (days === 1) return 'вчера'
        if (days < 7) return `${days} дн. назад`
        return new Date(vacancy.published_at).toLocaleDateString('ru-RU', {
          day: 'numeric', month: 'short',
        })
      })()
    : null

  const desc = vacancy.description
    ? vacancy.description.length > 200
      ? vacancy.description.slice(0, 200).split(' ').slice(0, -1).join(' ') + '...'
      : vacancy.description
    : null

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow flex flex-col"
      role="article"
      aria-label={`Вакансия: ${vacancy.title}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-snug line-clamp-2">
          {vacancy.title}
        </h3>
        {vacancy.source && (
          <span
            className={`shrink-0 px-2 py-0.5 text-[10px] font-medium rounded-full ${
              sourceColors[vacancy.source] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            {sourceLabels[vacancy.source] || vacancy.source}
          </span>
        )}
      </div>

      {/* Company + City */}
      <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2 flex-wrap">
        {vacancy.company && (
          <span className="flex items-center gap-1">
            <span>🏢</span> {vacancy.company}
          </span>
        )}
        {vacancy.city && (
          <span className="flex items-center gap-1">
            <span>📍</span> {vacancy.city}
          </span>
        )}
        {timeAgo && (
          <span className="flex items-center gap-1 ml-auto text-gray-400 dark:text-gray-500">
            <span>🕐</span> {timeAgo}
          </span>
        )}
      </div>

      {/* Salary */}
      {vacancy.salary_text && (
        <div className="text-sm font-medium text-green-600 dark:text-green-400 mb-2">
          💰 {vacancy.salary_text}
        </div>
      )}

      {/* Employment + Experience chips */}
      <div className="flex flex-wrap gap-1 mb-2">
        {empLabel && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            👔 {empLabel}
          </span>
        )}
        {vacancy.experience && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
            💼 {config.experiences[vacancy.experience] || vacancy.experience}
          </span>
        )}
      </div>

      {/* Description */}
      {desc && (
        <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-3 line-clamp-3">
          📋 {desc}
        </p>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Link */}
      <a
        href={vacancy.url}
        target="_blank"
        rel="noopener noreferrer"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => handleKeyDown(e, vacancy.url)}
        tabIndex={0}
        aria-label={`Открыть вакансию ${vacancy.title}`}
        className="inline-flex items-center justify-center gap-1 px-3 py-1.5 text-xs font-medium text-primary border border-primary rounded-lg hover:bg-primary hover:text-white transition-colors self-start"
      >
        🔗 Открыть вакансию
      </a>
    </div>
  )
}

import type { SavedVacancy, AppConfig } from '../types'

interface SavedPanelProps {
  saved: SavedVacancy[]
  config: AppConfig
}

export default function SavedPanel({ saved, config }: SavedPanelProps) {
  if (saved.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p className="text-sm mb-1">📌 Нет сохранённых вакансий</p>
        <p className="text-xs">Сохраняй вакансии из результатов кнопкой 📌</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {saved.map((v) => {
        const timeAgo = v.saved_at
          ? (() => {
              const diff = Date.now() - new Date(v.saved_at).getTime()
              const days = Math.floor(diff / 86400000)
              if (days === 0) return 'сегодня'
              if (days === 1) return 'вчера'
              return `${days} дн. назад`
            })()
          : ''

        return (
          <a
            key={v.id}
            href={v.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3.5 hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 transition-all"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">{v.vacancy_title}</p>
                <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 flex-wrap">
                  {v.company && <span>🏢 {v.company}</span>}
                  {v.salary_text && <span className="text-emerald-600 dark:text-emerald-400 font-medium">💰 {v.salary_text}</span>}
                </div>
              </div>
              <div className="flex flex-col items-end gap-1 shrink-0">
                <span className="px-2 py-0.5 text-[10px] rounded-md bg-gray-100 dark:bg-gray-700 text-gray-500">
                  {config.sites[v.source] || v.source}
                </span>
                {timeAgo && <span className="text-[10px] text-gray-400 whitespace-nowrap">📌 {timeAgo}</span>}
              </div>
            </div>
          </a>
        )
      })}
    </div>
  )
}

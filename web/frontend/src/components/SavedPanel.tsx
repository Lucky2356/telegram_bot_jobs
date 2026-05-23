import type { SavedVacancy, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import { ExternalLink, Trash2 } from 'lucide-react'

interface SavedPanelProps {
  saved: SavedVacancy[]
  config: AppConfig
  onRefresh: () => void
}

export default function SavedPanel({ saved, config, onRefresh }: SavedPanelProps) {
  const handleDelete = async (id: number) => {
    try {
      await api.deleteSaved(id)
      toast.success('Удалено из избранного')
      onRefresh()
    } catch {
      toast.error('Ошибка')
    }
  }

  if (saved.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
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
          <div
            key={v.id}
            className="flex items-start justify-between gap-3 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 p-3.5 hover:shadow-md transition-shadow"
          >
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-900 dark:text-slate-100 truncate">{v.vacancy_title}</p>
              <div className="flex items-center gap-2 mt-1 text-xs text-slate-500 flex-wrap">
                {v.company && <span>🏢 {v.company}</span>}
                {v.salary_text && <span className="text-emerald-600 dark:text-emerald-400 font-medium">💰 {v.salary_text}</span>}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <div className="flex items-center gap-1">
                <a
                  href={v.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="p-1 rounded text-slate-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                  aria-label="Открыть"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                </a>
                <button
                  onClick={() => handleDelete(v.id)}
                  className="p-1 rounded text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                  aria-label="Удалить из избранного"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              <span className="px-2 py-0.5 text-[10px] rounded-md bg-slate-100 dark:bg-slate-800 text-slate-500">
                {config.sites[v.source] || v.source}
              </span>
              {timeAgo && <span className="text-[10px] text-slate-400 whitespace-nowrap">📌 {timeAgo}</span>}
            </div>
          </div>
        )
      })}
    </div>
  )
}

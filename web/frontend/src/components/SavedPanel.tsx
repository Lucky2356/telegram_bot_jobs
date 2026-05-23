import { Trash2, ExternalLink, BookmarkCheck } from 'lucide-react'
import type { SavedVacancy, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface SavedPanelProps {
  saved: SavedVacancy[]
  config: AppConfig
  onRefresh: () => void
}

function timeAgo(savedAt: string) {
  const diff = Date.now() - new Date(savedAt).getTime()
  const days = Math.floor(diff / 86400000)
  if (days <= 0) return 'сегодня'
  if (days === 1) return 'вчера'
  return `${days} дн. назад`
}

export default function SavedPanel({ saved, config, onRefresh }: SavedPanelProps) {
  const handleDelete = async (id: number) => {
    try {
      await api.deleteSaved(id)
      toast.success('Удалено из избранного')
      onRefresh()
    } catch {
      toast.error('Не удалось удалить вакансию')
    }
  }

  if (saved.length === 0) {
    return (
      <div className="rounded-xl border border-dashed border-[var(--border)] bg-[color:var(--surface-elevated)] p-8 text-center">
        <p className="text-base font-medium text-primary">В избранном пока пусто</p>
        <p className="mt-2 text-sm text-secondary">Сохраняйте вакансии из ленты и возвращайтесь к ним позже.</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {saved.map((vacancy) => (
        <article
          key={vacancy.id}
          className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3 transition hover:border-[var(--border-strong)]"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-primary">{vacancy.vacancy_title}</p>
              <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-secondary">
                {vacancy.company && <span>{vacancy.company}</span>}
                {vacancy.salary_text && <span className="font-semibold text-emerald-400">{vacancy.salary_text}</span>}
                {vacancy.city && <span>{vacancy.city}</span>}
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-1">
              <a
                href={vacancy.url}
                target="_blank"
                rel="noopener noreferrer"
                className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary transition hover:text-primary"
                aria-label="Открыть вакансию"
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
              <button
                onClick={() => handleDelete(vacancy.id)}
                className="focus-ring inline-flex h-8 w-8 items-center justify-center rounded-lg border border-rose-400/30 bg-rose-500/10 text-rose-300 transition hover:bg-rose-500/20"
                aria-label="Удалить из избранного"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>

          <div className="mt-2 flex items-center justify-between text-[11px] text-muted">
            <span className="inline-flex items-center gap-1">
              <BookmarkCheck className="h-3.5 w-3.5" />
              {timeAgo(vacancy.saved_at)}
            </span>
            <span>{config.sites[vacancy.source] || vacancy.source}</span>
          </div>
        </article>
      ))}
    </div>
  )
}

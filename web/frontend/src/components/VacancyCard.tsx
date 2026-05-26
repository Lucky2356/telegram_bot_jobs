import { memo, useMemo, useState } from 'react'
import { BookmarkPlus, Ban, ExternalLink, Flame, Sparkles, ThumbsDown } from 'lucide-react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface VacancyCardProps {
  vacancy: VacancyResult
  config: AppConfig
  showActions?: boolean
  onDetail?: (vacancy: VacancyResult) => void
}

const sourceStyles: Record<string, { label: string; className: string }> = {
  hh: { label: 'hh.ru', className: 'bg-blue-500/15 text-blue-300 border-blue-400/25' },
  superjob: { label: 'SuperJob', className: 'bg-cyan-500/15 text-cyan-300 border-cyan-400/25' },
  trudvsem: { label: 'Работа России', className: 'bg-emerald-500/15 text-emerald-300 border-emerald-400/25' },
  rabota: { label: 'rabota.ru', className: 'bg-amber-500/15 text-amber-300 border-amber-400/25' },
  habr: { label: 'Хабр Карьера', className: 'bg-rose-500/15 text-rose-300 border-rose-400/25' },
}

function timeAgoLabel(isoDate: string | null) {
  if (!isoDate) return null
  const diff = Date.now() - new Date(isoDate).getTime()
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return 'только что'
  if (hours < 24) return `${hours} ч. назад`
  const days = Math.floor(hours / 24)
  if (days === 1) return 'вчера'
  if (days < 7) return `${days} дн. назад`
  return new Date(isoDate).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

const VacancyCard = memo(function VacancyCard({ vacancy, config, showActions = true, onDetail }: VacancyCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [blocking, setBlocking] = useState(false)
  const [reporting, setReporting] = useState(false)

  const source = sourceStyles[vacancy.source] || { label: vacancy.source, className: 'bg-slate-500/10 text-slate-300 border-slate-500/20' }
  const empLabel = vacancy.employment_type ? config.employment_types[vacancy.employment_type] || vacancy.employment_type : null
  const timeAgo = timeAgoLabel(vacancy.published_at)

  const tags = useMemo(() => {
    if (!vacancy.description) return []
    const known = ['React', 'TypeScript', 'Python', 'Django', 'Node.js', 'Go', 'Kubernetes', 'AWS', 'Docker']
    const text = vacancy.description.toLowerCase()
    return known.filter((tag) => text.includes(tag.toLowerCase())).slice(0, 4)
  }, [vacancy.description])

  const shortDescription = useMemo(() => {
    if (!vacancy.description) return null
    if (expanded || vacancy.description.length <= 180) return vacancy.description
    const cut = vacancy.description.slice(0, 180)
    const safe = cut.lastIndexOf(' ')
    return `${safe > 0 ? cut.slice(0, safe) : cut}...`
  }, [vacancy.description, expanded])

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (saving) return
    setSaving(true)
    try {
      await api.saveVacancy(vacancy.id)
      toast.success('Вакансия добавлена в избранное')
    } catch {
      toast.error('Не удалось сохранить вакансию')
    } finally {
      setSaving(false)
    }
  }

  const handleBlock = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (blocking) return
    setBlocking(true)
    try {
      await api.blockVacancy(vacancy.id)
      toast.success('Компания добавлена в блок-лист')
    } catch {
      toast.error('Не удалось обновить блок-лист')
    } finally {
      setBlocking(false)
    }
  }

  const handleBadResult = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (reporting) return
    setReporting(true)
    try {
      const data = await api.reportBadVacancy(vacancy.id, vacancy.filter_id)
      if (data.applied.length > 0) {
        toast.success(`Добавлено в исключения: ${data.applied.join(', ')}`)
      } else if (data.suggestions.length > 0) {
        toast.success(`Есть предложения: ${data.suggestions.join(', ')}`)
      } else {
        toast.success('Отзыв учтен')
      }
    } catch {
      toast.error('Не удалось отправить отзыв')
    } finally {
      setReporting(false)
    }
  }

  const isFresh = vacancy.published_at
    ? Date.now() - new Date(vacancy.published_at).getTime() <= 1000 * 60 * 60 * 12
    : false

  const handleCardClick = () => onDetail?.(vacancy)

  return (
    <article
      onClick={handleCardClick}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          handleCardClick()
        }
      }}
      className="group bento-card flex h-full cursor-pointer flex-col overflow-hidden p-4"
      role="article"
      tabIndex={0}
      aria-label={`Вакансия: ${vacancy.title}`}
    >
      <div className="flex items-start justify-between gap-3">
        <h3 className="line-clamp-2 text-sm font-semibold leading-snug text-primary md:text-[15px]">
          {vacancy.title}
        </h3>
        <div className="flex flex-col items-end gap-1">
          <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-[10px] font-semibold ${source.className}`}>
            {source.label}
          </span>
          {typeof vacancy.score === 'number' && (
            <span className="inline-flex items-center rounded-full border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2 py-0.5 text-[10px] font-semibold text-secondary">
              {vacancy.score}
            </span>
          )}
          {isFresh && (
            <span className="inline-flex items-center gap-1 rounded-full border border-rose-400/25 bg-rose-500/10 px-2 py-0.5 text-[10px] font-semibold text-rose-300">
              <Flame className="h-3 w-3" />
              Новая
            </span>
          )}
        </div>
      </div>

      <div className="mt-2 flex items-center gap-2 text-xs text-secondary">
        {vacancy.company && <span className="truncate font-medium text-primary">{vacancy.company}</span>}
        {timeAgo && <span className="ml-auto text-muted">{timeAgo}</span>}
      </div>

      {vacancy.salary_text && (
        <p className="mt-2 text-sm font-bold text-emerald-400">{vacancy.salary_text}</p>
      )}

      <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] text-secondary">
        {vacancy.city && <span className="rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2 py-1">{vacancy.city}</span>}
        {empLabel && <span className="rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2 py-1">{empLabel}</span>}
        {vacancy.experience && (
          <span className="rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2 py-1">
            {config.experiences[vacancy.experience] || vacancy.experience}
          </span>
        )}
      </div>

      {tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span key={tag} className="inline-flex items-center rounded-md bg-[var(--accent-soft)] px-2 py-0.5 text-[10px] font-medium text-primary">
              {tag}
            </span>
          ))}
        </div>
      )}

      {shortDescription && (
        <div className="mt-2 text-xs leading-relaxed text-secondary">
          {shortDescription}
          {vacancy.description && vacancy.description.length > 180 && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                setExpanded((prev) => !prev)
              }}
              className="focus-ring ml-1 rounded px-1 text-[var(--accent)] hover:underline"
            >
              {expanded ? 'Свернуть' : 'Ещё'}
            </button>
          )}
        </div>
      )}

      <div className="mt-auto" />

      {showActions && (
        <div className="mt-3 grid grid-cols-4 gap-2 pt-3">
          <a
            href={vacancy.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="focus-ring col-span-1 inline-flex h-9 min-w-0 items-center justify-center gap-1 rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] px-1 text-[11px] font-semibold text-primary transition hover:border-[var(--border-strong)] sm:text-xs"
            aria-label={`Открыть вакансию ${vacancy.title}`}
          >
            <ExternalLink className="h-3.5 w-3.5" />
            <span className="btn-text">Открыть</span>
          </a>
          <button
            onClick={handleSave}
            disabled={saving}
            className="focus-ring col-span-1 inline-flex h-9 min-w-0 items-center justify-center gap-1 rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] px-1 text-[11px] font-semibold text-primary transition hover:border-[var(--border-strong)] disabled:cursor-not-allowed disabled:opacity-50 sm:text-xs"
            aria-label="Сохранить вакансию"
          >
            <BookmarkPlus className="h-3.5 w-3.5" />
            <span className="btn-text">{saving ? '...' : 'Сохранить'}</span>
          </button>
          <button
            onClick={handleBlock}
            disabled={blocking}
            className="focus-ring col-span-1 inline-flex h-9 min-w-0 items-center justify-center gap-1 rounded-lg border border-rose-400/25 bg-rose-500/10 px-1 text-[11px] font-semibold text-rose-300 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-50 sm:text-xs"
            aria-label="Скрыть похожие вакансии компании"
          >
            <Ban className="h-3.5 w-3.5" />
            <span className="btn-text">{blocking ? '...' : 'Скрыть'}</span>
          </button>
          <button
            onClick={handleBadResult}
            disabled={reporting}
            className="focus-ring col-span-1 inline-flex h-9 min-w-0 items-center justify-center gap-1 rounded-lg border border-amber-400/25 bg-amber-500/10 px-1 text-[11px] font-semibold text-amber-300 transition hover:bg-amber-500/20 disabled:cursor-not-allowed disabled:opacity-50 sm:text-xs"
            aria-label="Отметить вакансию как плохой результат"
          >
            <ThumbsDown className="h-3.5 w-3.5" />
            <span className="btn-text">{reporting ? '...' : 'Плохая'}</span>
          </button>
        </div>
      )}

      {vacancy.filter_name && (
        <div className="mt-3 inline-flex w-fit items-center gap-1 rounded-full border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2 py-1 text-[10px] font-medium text-secondary">
          <Sparkles className="h-3 w-3 text-[var(--accent)]" />
          {vacancy.filter_name}
        </div>
      )}
    </article>
  )
})

export default VacancyCard

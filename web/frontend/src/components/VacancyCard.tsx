import { useState, memo } from 'react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'

interface VacancyCardProps {
  vacancy: VacancyResult
  config: AppConfig
  showActions?: boolean
  onDetail?: (vacancy: VacancyResult) => void
}

const sourceStyles: Record<string, { label: string; color: string }> = {
  hh: { label: 'hh.ru', color: 'bg-blue-600' },
  superjob: { color: 'bg-cyan-600', label: 'SuperJob' },
  trudvsem: { color: 'bg-emerald-600', label: 'Работа России' },
  rabota: { color: 'bg-amber-600', label: 'rabota.ru' },
  habr: { color: 'bg-rose-600', label: 'Хабр Карьера' },
}

const VacancyCard = memo(function VacancyCard({ vacancy, config, showActions = true, onDetail }: VacancyCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)
  const [blocking, setBlocking] = useState(false)
  const src = vacancy.source ? sourceStyles[vacancy.source] : null

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
        return new Date(vacancy.published_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
      })()
    : null

  const handleSave = async (e: React.MouseEvent) => {
    e.stopPropagation()
    if (saving) return
    setSaving(true)
    try {
      await api.saveVacancy(vacancy.id)
      toast.success('✅ Вакансия сохранена')
    } catch {
      toast.error('Ошибка сохранения')
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
      toast.success('🚫 Компания добавлена в блок-лист')
    } catch {
      toast.error('Ошибка')
    } finally {
      setBlocking(false)
    }
  }

  const descTruncated = (vacancy.description?.length ?? 0) > 150
  const truncateDesc = (desc: string, maxLen: number) => {
    if (desc.length <= maxLen) return desc
    const truncated = desc.slice(0, maxLen)
    const lastSpace = truncated.lastIndexOf(' ')
    return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '...'
  }
  const desc = expanded && vacancy.description ? vacancy.description
    : descTruncated && vacancy.description
      ? truncateDesc(vacancy.description, 150)
      : vacancy.description

  const handleCardClick = () => onDetail?.(vacancy)

  return (
    <div
      onClick={handleCardClick}
      onKeyDown={(e) => { if (e.key === 'Enter') handleCardClick() }}
      className="relative bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 flex flex-col overflow-hidden group cursor-pointer"
      role="article"
      tabIndex={0}
      aria-label={`Вакансия: ${vacancy.title}`}
    >
      {src && <div className={`absolute top-0 left-0 w-0.5 h-full ${src.color}`} />}

      <div className="p-3.5 pl-4 flex flex-col flex-1">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 leading-snug line-clamp-2 flex-1">
            {vacancy.title}
          </h3>
          <div className="shrink-0 flex flex-col items-end gap-1">
            {vacancy.filter_name && (
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                {vacancy.filter_name}
              </span>
            )}
            {src && (
              <span className={`px-2 py-0.5 text-[10px] font-semibold rounded-full text-white ${src.color}`}>
                {src.label}
              </span>
            )}
          </div>
        </div>

        {vacancy.company && (
          <p className="text-xs text-slate-500 dark:text-slate-400 mb-1.5 font-medium">
            {vacancy.company}
          </p>
        )}

        {vacancy.salary_text && (
          <div className="text-sm font-bold text-emerald-600 dark:text-emerald-400 mb-2">
            {vacancy.salary_text}
          </div>
        )}

        <div className="flex items-center gap-2 text-xs text-slate-400 dark:text-slate-500 mb-2 flex-wrap">
          {vacancy.city && <span>📍 {vacancy.city}</span>}
          {empLabel && <span>👔 {empLabel}</span>}
          {vacancy.experience && <span>💼 {config.experiences[vacancy.experience] || vacancy.experience}</span>}
          {timeAgo && <span className="ml-auto">🕐 {timeAgo}</span>}
        </div>

        {desc && (
          <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-2">
            {desc}
            {descTruncated && (
              <button
                onClick={(e) => { e.stopPropagation(); setExpanded(!expanded) }}
                className="ml-1 text-blue-600 dark:text-blue-400 hover:underline font-medium cursor-pointer"
              >
                {expanded ? 'свернуть' : 'показать ещё'}
              </button>
            )}
          </div>
        )}

        <div className="flex-1" />

        {showActions && (
          <div className="flex items-center gap-2 mt-2 pt-2.5 border-t border-slate-100 dark:border-slate-800 flex-wrap">
            <a
              href={vacancy.url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 dark:hover:text-white transition-colors"
              aria-label={`Открыть ${vacancy.title}`}
            >
              🔗 Открыть
            </a>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors cursor-pointer disabled:opacity-50"
              aria-label="Сохранить"
            >
              {saving ? '⏳' : '📌'}
            </button>
            <button
              onClick={handleBlock}
              disabled={blocking}
              className="px-3 py-2 text-xs rounded-lg border border-slate-200 dark:border-slate-700 hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-red-500 transition-colors cursor-pointer disabled:opacity-50"
              aria-label="Не интересует"
            >
              {blocking ? '⏳' : '🚫'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
})

export default VacancyCard

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

const sourceStyles: Record<string, { label: string; color: string; stripe: string }> = {
  hh: { label: 'hh.ru', color: 'bg-blue-50 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300', stripe: 'bg-blue-500' },
  superjob: { color: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-300', stripe: 'bg-cyan-500', label: 'SuperJob' },
  trudvsem: { color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300', stripe: 'bg-emerald-500', label: 'Работа России' },
  rabota: { color: 'bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300', stripe: 'bg-amber-500', label: 'rabota.ru' },
  habr: { color: 'bg-rose-50 text-rose-700 dark:bg-rose-900/30 dark:text-rose-300', stripe: 'bg-rose-500', label: 'Хабр Карьера' },
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

  const handleSave = async () => {
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

  const handleBlock = async () => {
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

  const descTruncated = (vacancy.description?.length ?? 0) > 180
  const desc = expanded && vacancy.description ? vacancy.description
    : descTruncated && vacancy.description
      ? vacancy.description.slice(0, 180).split(' ').slice(0, -1).join(' ') + '...'
      : vacancy.description

  return (
    <div
      onClick={() => onDetail?.(vacancy)}
      onKeyDown={(e) => { if (e.key === 'Enter') onDetail?.(vacancy) }}
      className="relative bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 hover:shadow-md hover:border-slate-300/80 dark:hover:border-slate-600/60 transition-all duration-200 flex flex-col overflow-hidden group cursor-pointer"
      role="article"
      tabIndex={0}
      aria-label={`Вакансия: ${vacancy.title}`}
    >
      {/* Accent stripe */}
      {src && <div className={`absolute top-0 left-0 w-1 h-full ${src.stripe} opacity-40`} />}

      <div className="p-4 pl-5 flex flex-col flex-1">
        {/* Header */}
        <div className="flex items-start justify-between gap-2 mb-2.5">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100 leading-snug line-clamp-2 flex-1">
            {vacancy.title}
          </h3>
          <div className="shrink-0 flex flex-col items-end gap-1">
            {vacancy.filter_name && (
              <span className="px-2 py-0.5 text-[10px] font-medium rounded-lg bg-primary/10 text-primary">
                📋 {vacancy.filter_name}
              </span>
            )}
            {src && (
              <span className={`px-2.5 py-1 text-[10px] font-semibold rounded-lg ${src.color}`}>
                {src.label}
              </span>
            )}
          </div>
        </div>

        {/* Company + City + Time */}
        <div className="flex items-center gap-2.5 text-xs text-slate-500 dark:text-slate-400 mb-2.5 flex-wrap">
          {vacancy.company && (
            <span className="flex items-center gap-1.5">
              <span>🏢</span>
              <span className="font-medium text-slate-700 dark:text-slate-300">{vacancy.company}</span>
            </span>
          )}
          {vacancy.city && (
            <span className="flex items-center gap-1.5">📍 {vacancy.city}</span>
          )}
          {timeAgo && <span className="flex items-center gap-1.5 ml-auto text-slate-400 dark:text-slate-500">🕐 {timeAgo}</span>}
        </div>

        {/* Salary */}
        {vacancy.salary_text && (
          <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 mb-2.5 bg-emerald-50/70 dark:bg-emerald-900/15 px-3 py-1 rounded-lg inline-block">
            💰 {vacancy.salary_text}
          </div>
        )}

        {/* Employment + Experience */}
        {(empLabel || vacancy.experience) && (
          <div className="flex flex-wrap gap-1.5 mb-2.5">
            {empLabel && <span className="px-2.5 py-1 text-[11px] rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 font-medium">👔 {empLabel}</span>}
            {vacancy.experience && <span className="px-2.5 py-1 text-[11px] rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 font-medium">💼 {config.experiences[vacancy.experience] || vacancy.experience}</span>}
          </div>
        )}

        {/* Description */}
        {desc && (
          <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed mb-2.5">
            📋 {desc}
            {descTruncated && (
              <button
                onClick={() => setExpanded(!expanded)}
                className="ml-1 text-primary hover:underline font-medium cursor-pointer"
              >
                {expanded ? 'свернуть' : 'показать ещё'}
              </button>
            )}
          </div>
        )}

        <div className="flex-1" />

        {/* Actions */}
        {showActions && (
          <div className="flex items-center gap-2 mt-2 pt-3 border-t border-slate-100 dark:border-slate-700/40">
            <a
              href={vacancy.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium text-primary bg-primary/5 border border-primary/20 rounded-xl hover:bg-primary hover:text-white transition-all"
              aria-label={`Открыть ${vacancy.title}`}
            >
              🔗 Открыть
            </a>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700/60 hover:bg-slate-100 dark:hover:bg-slate-700/60 text-slate-500 dark:text-slate-400 transition-all cursor-pointer disabled:opacity-50"
              aria-label="Сохранить"
            >
              {saving ? '⏳' : '📌'}
            </button>
            <button
              onClick={handleBlock}
              disabled={blocking}
              className="px-3 py-2 text-xs rounded-xl border border-slate-200 dark:border-slate-700/60 hover:bg-red-50 dark:hover:bg-red-900/10 text-slate-400 hover:text-red-500 transition-all cursor-pointer disabled:opacity-50"
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

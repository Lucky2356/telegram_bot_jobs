import { useState } from 'react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'

interface VacancyCardProps {
  vacancy: VacancyResult
  config: AppConfig
  showActions?: boolean
}

const sourceColors: Record<string, string> = {
  hh: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300 border-blue-200 dark:border-blue-800',
  superjob: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/20 dark:text-cyan-300 border-cyan-200 dark:border-cyan-800',
  trudvsem: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300 border-emerald-200 dark:border-emerald-800',
  rabota: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300 border-amber-200 dark:border-amber-800',
  habr: 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300 border-rose-200 dark:border-rose-800',
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России',
  rabota: 'rabota.ru', habr: 'Хабр Карьера',
}

export default function VacancyCard({ vacancy, config, showActions = true }: VacancyCardProps) {
  const [expanded, setExpanded] = useState(false)
  const [saving, setSaving] = useState(false)

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

  const descTruncated = (vacancy.description?.length ?? 0) > 180
  const desc = expanded && vacancy.description ? vacancy.description
    : descTruncated && vacancy.description
      ? vacancy.description.slice(0, 180).split(' ').slice(0, -1).join(' ') + '...'
      : vacancy.description

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.checkNow()
      toast.success('Сохранено!')
    } catch { toast.error('Ошибка') }
    finally { setSaving(false) }
  }

  const handleBlock = () => {
    toast.info('Блокировка пока только в Telegram')
  }

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 flex flex-col"
      role="article"
      aria-label={`Вакансия: ${vacancy.title}`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 mb-2.5">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100 leading-snug line-clamp-2 flex-1">
          {vacancy.title}
        </h3>
        {vacancy.source && (
          <span className={`shrink-0 px-2 py-0.5 text-[10px] font-semibold rounded-md border ${
            sourceColors[vacancy.source] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400 border-gray-200'
          }`}>
            {sourceLabels[vacancy.source] || vacancy.source}
          </span>
        )}
      </div>

      {/* Company + City + Time */}
      <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400 mb-2.5 flex-wrap">
        {vacancy.company && (
          <span className="flex items-center gap-1.5">
            <span className="text-gray-400">🏢</span>
            <span className="font-medium text-gray-600 dark:text-gray-300">{vacancy.company}</span>
          </span>
        )}
        {vacancy.city && (
          <span className="flex items-center gap-1.5">
            <span className="text-gray-400">📍</span>{vacancy.city}
          </span>
        )}
        {timeAgo && <span className="flex items-center gap-1.5 ml-auto text-gray-400 dark:text-gray-500">🕐 {timeAgo}</span>}
      </div>

      {/* Salary */}
      {vacancy.salary_text && (
        <div className="text-sm font-semibold text-emerald-600 dark:text-emerald-400 mb-2.5 bg-emerald-50 dark:bg-emerald-900/10 px-3 py-1 rounded-md inline-block">
          💰 {vacancy.salary_text}
        </div>
      )}

      {/* Employment + Experience */}
      {(empLabel || vacancy.experience) && (
        <div className="flex flex-wrap gap-1.5 mb-2.5">
          {empLabel && (
            <span className="px-2.5 py-0.5 text-[11px] rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium">
              👔 {empLabel}
            </span>
          )}
          {vacancy.experience && (
            <span className="px-2.5 py-0.5 text-[11px] rounded-md bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 font-medium">
              💼 {config.experiences[vacancy.experience] || vacancy.experience}
            </span>
          )}
        </div>
      )}

      {/* Description */}
      {desc && (
        <div className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed mb-2">
          📋 {desc}
          {descTruncated && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="ml-1 text-primary hover:underline font-medium cursor-pointer"
              aria-label={expanded ? 'Свернуть' : 'Показать ещё'}
            >
              {expanded ? 'свернуть' : 'показать ещё'}
            </button>
          )}
        </div>
      )}

      <div className="flex-1" />

      {/* Actions */}
      {showActions && (
        <div className="flex items-center gap-2 mt-2.5 pt-2.5 border-t border-gray-100 dark:border-gray-700">
          <a
            href={vacancy.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-xs font-medium text-primary border border-primary/30 rounded-lg hover:bg-primary hover:text-white transition-all"
            aria-label={`Открыть ${vacancy.title}`}
          >
            🔗 Открыть
          </a>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-3 py-2 text-xs font-medium border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-400 transition-all cursor-pointer disabled:opacity-50"
            aria-label="Сохранить вакансию"
          >
            📌
          </button>
          <button
            onClick={handleBlock}
            className="px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/10 text-gray-400 hover:text-red-500 transition-all cursor-pointer"
            aria-label="Не интересует"
          >
            🚫
          </button>
        </div>
      )}
    </div>
  )
}

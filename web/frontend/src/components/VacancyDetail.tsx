import { useState, useEffect } from 'react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import { X, ExternalLink, Bookmark, Ban } from 'lucide-react'

interface VacancyDetailProps {
  vacancy: VacancyResult
  config: AppConfig
  onClose: () => void
  onSaved?: () => void
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России',
  rabota: 'rabota.ru', habr: 'Хабр Карьера',
}

export default function VacancyDetail({ vacancy, config, onClose, onSaved }: VacancyDetailProps) {
  const [saving, setSaving] = useState(false)
  const [blocking, setBlocking] = useState(false)

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  const handleSave = async () => {
    if (saving) return
    setSaving(true)
    try {
      await api.saveVacancy(vacancy.id)
      toast.success('✅ Сохранено')
      onSaved?.()
    } catch {
      toast.error('Ошибка')
    } finally {
      setSaving(false)
    }
  }

  const handleBlock = async () => {
    if (blocking) return
    setBlocking(true)
    try {
      await api.blockVacancy(vacancy.id)
      toast.success('🚫 Компания в блок-листе')
    } catch {
      toast.error('Ошибка')
    } finally {
      setBlocking(false)
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
        return new Date(vacancy.published_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
      })()
    : null

  return (
    <div
      className="fixed inset-0 z-40 flex justify-end"
      role="dialog"
      aria-modal="true"
      aria-label={vacancy.title}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-950/30" onClick={onClose} />

      {/* Drawer */}
      <div className="relative w-full max-w-xl bg-white dark:bg-slate-900 shadow-2xl border-l border-slate-200 dark:border-slate-800 h-full overflow-y-auto flex flex-col">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-900 z-10 flex items-start justify-between px-6 pt-5 pb-3 border-b border-slate-200 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 leading-snug pr-4">
            {vacancy.title}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 shrink-0 flex items-center justify-center rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer transition-colors"
            aria-label="Закрыть"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 px-6 py-4 space-y-4">
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-1 text-[10px] font-semibold rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
              {sourceLabels[vacancy.source] || vacancy.source}
            </span>
            {vacancy.filter_name && (
              <span className="px-2.5 py-1 text-[10px] font-medium rounded-lg bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400">
                {vacancy.filter_name}
              </span>
            )}
            {timeAgo && (
              <span className="text-[10px] text-slate-400">🕐 {timeAgo}</span>
            )}
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-slate-600 dark:text-slate-400">
            {vacancy.company && (
              <span className="flex items-center gap-1.5">
                <span className="font-medium text-slate-800 dark:text-slate-200">{vacancy.company}</span>
              </span>
            )}
            {vacancy.city && (
              <span className="flex items-center gap-1.5">📍 {vacancy.city}</span>
            )}
          </div>

          {vacancy.salary_text && (
            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/20 px-4 py-2 rounded-lg inline-block">
              {vacancy.salary_text}
            </div>
          )}

          {(empLabel || vacancy.experience) && (
            <div className="flex flex-wrap gap-2">
              {empLabel && (
                <span className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-medium">
                  👔 {empLabel}
                </span>
              )}
              {vacancy.experience && (
                <span className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-medium">
                  💼 {config.experiences[vacancy.experience] || vacancy.experience}
                </span>
              )}
            </div>
          )}

          {vacancy.description && (
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-4 border border-slate-200 dark:border-slate-700">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">Описание</h3>
              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {vacancy.description}
              </p>
            </div>
          )}

          {vacancy.published_at && (
            <p className="text-xs text-slate-400">
              Опубликовано: {new Date(vacancy.published_at).toLocaleString('ru-RU', {
                day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
              })}
            </p>
          )}
        </div>

        <div className="sticky bottom-0 bg-white dark:bg-slate-900 flex items-center justify-end gap-2 px-4 md:px-6 py-4 border-t border-slate-200 dark:border-slate-800 flex-wrap">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition-colors cursor-pointer disabled:opacity-50"
          >
            <Bookmark className="w-3.5 h-3.5" />
            {saving ? '⏳' : 'Сохранить'}
          </button>
          <button
            onClick={handleBlock}
            disabled={blocking}
            className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-500 hover:text-red-500 transition-colors cursor-pointer disabled:opacity-50"
          >
            <Ban className="w-3.5 h-3.5" />
            {blocking ? '⏳' : 'Заблокировать'}
          </button>
          <a
            href={vacancy.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 px-5 py-2 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors shadow-sm"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            Открыть
          </a>
        </div>
      </div>
    </div>
  )
}

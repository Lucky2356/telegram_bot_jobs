import { useState } from 'react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'

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
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/30 backdrop-blur-sm p-4"
      role="dialog"
      aria-modal="true"
      aria-label={vacancy.title}
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
    >
      <div className="bg-white/95 dark:bg-slate-800/95 backdrop-blur-lg rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto border border-slate-200/60 dark:border-slate-700/40">
        {/* Header */}
        <div className="sticky top-0 bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm z-10 flex items-center justify-between px-6 pt-5 pb-3 border-b border-slate-100 dark:border-slate-700/40">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100 leading-snug pr-4">
            {vacancy.title}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 shrink-0 flex items-center justify-center rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-4 space-y-4">
          {/* Meta badges */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-1 text-[10px] font-semibold rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400">
              {sourceLabels[vacancy.source] || vacancy.source}
            </span>
            {vacancy.filter_name && (
              <span className="px-2.5 py-1 text-[10px] font-medium rounded-lg bg-primary/10 text-primary">
                📋 {vacancy.filter_name}
              </span>
            )}
            {timeAgo && (
              <span className="text-[10px] text-slate-400">🕐 {timeAgo}</span>
            )}
          </div>

          {/* Company + City */}
          <div className="flex flex-wrap gap-4 text-sm text-slate-600 dark:text-slate-400">
            {vacancy.company && (
              <span className="flex items-center gap-1.5">
                <span>🏢</span>
                <span className="font-medium text-slate-800 dark:text-slate-200">{vacancy.company}</span>
              </span>
            )}
            {vacancy.city && (
              <span className="flex items-center gap-1.5">📍 {vacancy.city}</span>
            )}
          </div>

          {/* Salary */}
          {vacancy.salary_text && (
            <div className="text-lg font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-50/70 dark:bg-emerald-900/15 px-4 py-2 rounded-xl inline-block">
              💰 {vacancy.salary_text}
            </div>
          )}

          {/* Employment + Experience */}
          {(empLabel || vacancy.experience) && (
            <div className="flex flex-wrap gap-2">
              {empLabel && (
                <span className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 font-medium">
                  👔 {empLabel}
                </span>
              )}
              {vacancy.experience && (
                <span className="px-3 py-1.5 text-xs rounded-lg bg-slate-100 dark:bg-slate-700/60 text-slate-600 dark:text-slate-400 font-medium">
                  💼 {config.experiences[vacancy.experience] || vacancy.experience}
                </span>
              )}
            </div>
          )}

          {/* Full description */}
          {vacancy.description && (
            <div className="bg-slate-50/70 dark:bg-slate-900/70 rounded-xl p-4 border border-slate-200/60 dark:border-slate-700/40">
              <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">📋 Описание</h3>
              <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-line">
                {vacancy.description}
              </p>
            </div>
          )}

          {/* Published date */}
          {vacancy.published_at && (
            <p className="text-xs text-slate-400">
              Опубликовано: {new Date(vacancy.published_at).toLocaleString('ru-RU', {
                day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
              })}
            </p>
          )}
        </div>

        {/* Footer actions */}
        <div className="sticky bottom-0 bg-white/95 dark:bg-slate-800/95 backdrop-blur-sm flex items-center justify-end gap-2 px-6 py-4 border-t border-slate-100 dark:border-slate-700/40">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm font-medium border border-slate-200 dark:border-slate-700/60 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-400 transition-all cursor-pointer disabled:opacity-50"
          >
            {saving ? '⏳' : '📌 Сохранить'}
          </button>
          <button
            onClick={handleBlock}
            disabled={blocking}
            className="px-4 py-2 text-sm font-medium border border-slate-200 dark:border-slate-700/60 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/10 text-slate-500 hover:text-red-500 transition-all cursor-pointer disabled:opacity-50"
          >
            {blocking ? '⏳' : '🚫 Заблокировать'}
          </button>
          <a
            href={vacancy.url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-5 py-2 text-sm font-medium bg-primary text-white rounded-xl hover:bg-primary-hover transition-all shadow-sm"
          >
            🔗 Открыть на сайте
          </a>
        </div>
      </div>
    </div>
  )
}

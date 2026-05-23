import { useState, useEffect } from 'react'
import { X, ExternalLink, BookmarkPlus, Ban } from 'lucide-react'
import type { VacancyResult, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface VacancyDetailProps {
  vacancy: VacancyResult
  config: AppConfig
  onClose: () => void
  onSaved?: () => void
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru',
  superjob: 'SuperJob',
  trudvsem: 'Работа России',
  rabota: 'rabota.ru',
  habr: 'Хабр Карьера',
}

export default function VacancyDetail({ vacancy, config, onClose, onSaved }: VacancyDetailProps) {
  const [saving, setSaving] = useState(false)
  const [blocking, setBlocking] = useState(false)

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  const handleSave = async () => {
    if (saving) return
    setSaving(true)
    try {
      await api.saveVacancy(vacancy.id)
      toast.success('Вакансия сохранена')
      onSaved?.()
    } catch {
      toast.error('Не удалось сохранить вакансию')
    } finally {
      setSaving(false)
    }
  }

  const handleBlock = async () => {
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

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-end bg-slate-950/50 md:items-stretch" role="dialog" aria-modal="true" aria-label={vacancy.title} onClick={onClose}>
      <div className="h-full w-full max-w-2xl animate-soft-scale border-l border-[var(--border)] bg-[color:var(--surface-strong)] shadow-[var(--shadow-lg)]" onClick={(e) => e.stopPropagation()}>
        <div className="flex h-full flex-col">
          <header className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-[var(--border)] bg-[color:var(--surface)]/92 px-4 py-4 backdrop-blur md:px-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted">{sourceLabels[vacancy.source] || vacancy.source}</p>
              <h2 className="mt-1 text-base font-semibold leading-tight text-primary md:text-lg">{vacancy.title}</h2>
            </div>
            <button
              onClick={onClose}
              className="focus-ring inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary transition hover:text-primary"
              aria-label="Закрыть"
            >
              <X className="h-4 w-4" />
            </button>
          </header>

          <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4 md:px-6 md:py-5">
            <div className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <div className="flex flex-wrap items-center gap-2 text-xs text-secondary">
                {vacancy.company && <span className="font-semibold text-primary">{vacancy.company}</span>}
                {vacancy.city && <span>{vacancy.city}</span>}
                {vacancy.published_at && (
                  <span>{new Date(vacancy.published_at).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}</span>
                )}
              </div>

              {vacancy.salary_text && (
                <p className="mt-3 text-xl font-bold text-emerald-400">{vacancy.salary_text}</p>
              )}

              <div className="mt-3 flex flex-wrap gap-2 text-xs text-secondary">
                {vacancy.employment_type && (
                  <span className="rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] px-2.5 py-1">
                    {config.employment_types[vacancy.employment_type] || vacancy.employment_type}
                  </span>
                )}
                {vacancy.experience && (
                  <span className="rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] px-2.5 py-1">
                    {config.experiences[vacancy.experience] || vacancy.experience}
                  </span>
                )}
                {vacancy.filter_name && (
                  <span className="rounded-lg border border-[var(--border)] bg-[var(--accent-soft)] px-2.5 py-1 text-primary">
                    {vacancy.filter_name}
                  </span>
                )}
              </div>
            </div>

            <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Описание</h3>
              <p className="mt-3 whitespace-pre-line text-sm leading-relaxed text-secondary">
                {vacancy.description || 'Описание не предоставлено источником.'}
              </p>
            </section>
          </div>

          <footer className="sticky bottom-0 grid grid-cols-1 gap-2 border-t border-[var(--border)] bg-[color:var(--surface)]/95 px-4 py-3 backdrop-blur sm:grid-cols-3 md:px-6">
            <button
              onClick={handleSave}
              disabled={saving}
              className="focus-ring inline-flex h-10 items-center justify-center gap-1 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] text-sm font-semibold text-primary transition hover:border-[var(--border-strong)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <BookmarkPlus className="h-4 w-4" />
              {saving ? 'Сохраняем...' : 'Сохранить'}
            </button>
            <button
              onClick={handleBlock}
              disabled={blocking}
              className="focus-ring inline-flex h-10 items-center justify-center gap-1 rounded-xl border border-rose-400/30 bg-rose-500/10 text-sm font-semibold text-rose-300 transition hover:bg-rose-500/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Ban className="h-4 w-4" />
              {blocking ? 'Обновляем...' : 'Скрыть'}
            </button>
            <a
              href={vacancy.url}
              target="_blank"
              rel="noopener noreferrer"
              className="focus-ring inline-flex h-10 items-center justify-center gap-1 rounded-xl bg-[var(--accent)] text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
            >
              <ExternalLink className="h-4 w-4" />
              Открыть источник
            </a>
          </footer>
        </div>
      </div>

      <button
        className="sr-only"
        aria-label="Закрыть карточку вакансии"
        onClick={onClose}
      />
    </div>
  )
}

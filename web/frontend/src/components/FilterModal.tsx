import { useState, useEffect, type ReactNode } from 'react'
import { ChevronDown, X } from 'lucide-react'
import type { AppConfig, FilterFormData, VacancyFilter } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface FilterModalProps {
  config: AppConfig
  filter: VacancyFilter | null
  onClose: () => void
  onSaved: () => void
}

function buildInitialForm(filter: VacancyFilter | null): FilterFormData {
  if (!filter) {
    return {
      name: '',
      keywords: [],
      city: null,
      salary_min: null,
      salary_max: null,
      employment_types: [],
      sites: [],
      exclude_keywords: [],
      experience: null,
    }
  }

  return {
    name: filter.name,
    keywords: filter.keywords,
    city: filter.city,
    salary_min: filter.salary_min,
    salary_max: filter.salary_max,
    employment_types: filter.employment_types,
    sites: filter.sites,
    exclude_keywords: filter.exclude_keywords,
    experience: filter.experience,
  }
}

function ToggleChip({
  selected,
  onClick,
  children,
}: {
  selected: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={`focus-ring max-w-full rounded-lg border px-2.5 py-1.5 text-left text-xs font-medium leading-tight transition ${
        selected
          ? 'border-[var(--border-strong)] bg-[var(--accent-soft)] text-primary'
          : 'border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary hover:text-primary'
      }`}
    >
      <span className="block break-words">{children}</span>
    </button>
  )
}

export default function FilterModal({ config, filter, onClose, onSaved }: FilterModalProps) {
  const isEdit = filter !== null
  const [form, setForm] = useState<FilterFormData>(() => buildInitialForm(filter))
  const [saving, setSaving] = useState(false)
  const [keywordsOpen, setKeywordsOpen] = useState(true)
  const [excludeOpen, setExcludeOpen] = useState(false)

  useEffect(() => {
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onEscape)
    return () => document.removeEventListener('keydown', onEscape)
  }, [onClose])

  const toggleKeyword = (kw: string) => {
    setForm((prev) => ({
      ...prev,
      keywords: prev.keywords.includes(kw)
        ? prev.keywords.filter((item) => item !== kw)
        : [...prev.keywords, kw],
    }))
  }

  const toggleExclude = (kw: string) => {
    setForm((prev) => ({
      ...prev,
      exclude_keywords: prev.exclude_keywords.includes(kw)
        ? prev.exclude_keywords.filter((item) => item !== kw)
        : [...prev.exclude_keywords, kw],
    }))
  }

  const toggleEmployment = (key: string) => {
    setForm((prev) => ({
      ...prev,
      employment_types: prev.employment_types.includes(key)
        ? prev.employment_types.filter((item) => item !== key)
        : [...prev.employment_types, key],
    }))
  }

  const toggleSite = (key: string) => {
    setForm((prev) => ({
      ...prev,
      sites: prev.sites.includes(key)
        ? prev.sites.filter((item) => item !== key)
        : [...prev.sites, key],
    }))
  }

  const selectedSalary = config.salaries.find((s) => s[2] === form.salary_min && s[3] === form.salary_max)
  const salaryKey = selectedSalary ? selectedSalary[0] : 'any'

  const handleSalaryChange = (key: string) => {
    if (key === 'any') {
      setForm((prev) => ({ ...prev, salary_min: null, salary_max: null }))
      return
    }
    const selected = config.salaries.find((item) => item[0] === key)
    if (selected) {
      setForm((prev) => ({ ...prev, salary_min: selected[2], salary_max: selected[3] }))
    }
  }

  const handleSave = async () => {
    if (!form.name.trim()) {
      toast.error('Введите название фильтра')
      return
    }
    if (form.keywords.length === 0) {
      toast.error('Выберите ключевые слова')
      return
    }
    if (form.sites.length === 0) {
      toast.error('Выберите хотя бы один источник')
      return
    }

    setSaving(true)
    try {
      if (isEdit && filter) {
        await api.updateFilter(filter.id, form)
        toast.success('Фильтр обновлён')
      } else {
        await api.createFilter(form)
        toast.success('Фильтр создан')
      }
      onSaved()
      onClose()
    } catch {
      toast.error('Не удалось сохранить фильтр')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/60 p-0 md:items-center md:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={isEdit ? 'Редактирование фильтра' : 'Создание фильтра'}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="animate-soft-scale flex h-[92vh] w-full max-w-4xl flex-col rounded-t-3xl border border-[var(--border)] bg-[color:var(--surface-strong)] shadow-[var(--shadow-lg)] md:h-auto md:max-h-[92vh] md:rounded-2xl">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--border)] bg-[color:var(--surface)]/92 px-4 py-3 backdrop-blur md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Конструктор фильтра</p>
            <h2 className="text-base font-semibold text-primary md:text-lg">
              {isEdit ? 'Редактирование фильтра' : 'Создание фильтра'}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary transition hover:text-primary"
            aria-label="Закрыть"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="flex-1 space-y-4 overflow-y-auto px-4 py-4 md:px-6 md:py-5">
          <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
            <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Название фильтра</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              placeholder="Например: Frontend Middle"
              className="focus-ring mt-2 h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary placeholder:text-muted"
            />
          </section>

          <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
            <button
              onClick={() => setKeywordsOpen((prev) => !prev)}
              className="focus-ring flex w-full items-center justify-between rounded-lg text-left"
            >
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
                Ключевые слова ({form.keywords.length})
              </span>
              <ChevronDown className={`h-4 w-4 text-secondary transition ${keywordsOpen ? 'rotate-180' : ''}`} />
            </button>

            {keywordsOpen && (
              <div className="mt-3 space-y-3">
                {Object.entries(config.keyword_groups).map(([group, items]) => (
                  <div key={group}>
                    <p className="mb-1.5 text-xs font-semibold text-secondary">{group}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.keys(items).map((kw) => (
                        <ToggleChip key={kw} selected={form.keywords.includes(kw)} onClick={() => toggleKeyword(kw)}>
                          {kw}
                        </ToggleChip>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
            <button
              onClick={() => setExcludeOpen((prev) => !prev)}
              className="focus-ring flex w-full items-center justify-between rounded-lg text-left"
            >
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
                Исключить слова ({form.exclude_keywords.length})
              </span>
              <ChevronDown className={`h-4 w-4 text-secondary transition ${excludeOpen ? 'rotate-180' : ''}`} />
            </button>

            {excludeOpen && (
              <div className="mt-3 space-y-3">
                {Object.entries(config.keyword_groups).map(([group, items]) => (
                  <div key={group}>
                    <p className="mb-1.5 text-xs font-semibold text-secondary">{group}</p>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.keys(items).map((kw) => (
                        <ToggleChip key={kw} selected={form.exclude_keywords.includes(kw)} onClick={() => toggleExclude(kw)}>
                          {kw}
                        </ToggleChip>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Город</label>
              <select
                value={form.city ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value || null }))}
                className="focus-ring mt-2 h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
              >
                <option value="">Любой</option>
                {Object.entries(config.cities).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </section>

            <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Зарплата</label>
              <select
                value={salaryKey}
                onChange={(e) => handleSalaryChange(e.target.value)}
                className="focus-ring mt-2 h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
              >
                {config.salaries.map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </section>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Тип занятости</label>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {Object.entries(config.employment_types).map(([key, label]) => (
                  <ToggleChip
                    key={key}
                    selected={form.employment_types.includes(key)}
                    onClick={() => toggleEmployment(key)}
                  >
                    {label}
                  </ToggleChip>
                ))}
              </div>
            </section>

            <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Опыт</label>
              <select
                value={form.experience ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, experience: e.target.value || null }))}
                className="focus-ring mt-2 h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
              >
                <option value="">Любой</option>
                {Object.entries(config.experiences).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </section>
          </div>

          <section className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
            <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Источники ({form.sites.length})</label>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {Object.entries(config.sites).map(([key, label]) => (
                <ToggleChip key={key} selected={form.sites.includes(key)} onClick={() => toggleSite(key)}>
                  {label}
                </ToggleChip>
              ))}
            </div>
          </section>
        </div>

        <footer className="sticky bottom-0 grid grid-cols-2 gap-2 border-t border-[var(--border)] bg-[color:var(--surface)]/95 px-4 py-3 backdrop-blur md:flex md:justify-end md:px-6">
          <button
            onClick={onClose}
            className="focus-ring h-10 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-4 text-sm font-medium text-secondary transition hover:text-primary"
          >
            Отмена
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="focus-ring h-10 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {saving ? 'Сохранение...' : isEdit ? 'Сохранить изменения' : 'Создать фильтр'}
          </button>
        </footer>
      </div>
    </div>
  )
}


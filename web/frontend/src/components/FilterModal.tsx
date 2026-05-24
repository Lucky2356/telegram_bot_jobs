import { useState, useEffect, useMemo, type ReactNode } from 'react'
import { ChevronDown, Search, X } from 'lucide-react'
import type { AppConfig, FilterFormData, VacancyFilter } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface FilterModalProps {
  config: AppConfig
  filter: VacancyFilter | null
  onClose: () => void
  onSaved: (filter: VacancyFilter) => void
}

function unique(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim()).filter(Boolean)))
}

function buildInitialForm(filter: VacancyFilter | null, config: AppConfig): FilterFormData {
  if (!filter) {
    return {
      name: '',
      keywords: [],
      city: null,
      salary_min: null,
      salary_max: null,
      employment_types: [],
      sites: Object.keys(config.sites),
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
    sites: filter.sites.length ? filter.sites : Object.keys(config.sites),
    exclude_keywords: filter.exclude_keywords,
    experience: filter.experience,
  }
}

function buildAutoName(form: FilterFormData, config: AppConfig) {
  const keywords = form.keywords.slice(0, 2).join(', ') || 'Новый поиск'
  const city = form.city ? config.cities[form.city] || form.city : 'любой город'
  const salary = form.salary_min || form.salary_max
    ? `${form.salary_min ? `от ${form.salary_min.toLocaleString('ru-RU')}` : ''}${form.salary_min && form.salary_max ? ' ' : ''}${form.salary_max ? `до ${form.salary_max.toLocaleString('ru-RU')}` : ''} ₽`
    : ''
  return [keywords, city, salary].filter(Boolean).join(' · ')
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
      type="button"
      onClick={onClick}
      className={`focus-ring min-h-9 max-w-full rounded-xl border px-3 py-2 text-left text-xs font-semibold leading-tight transition hover:-translate-y-0.5 ${
        selected
          ? 'border-[var(--border-strong)] bg-[var(--accent-soft)] text-primary shadow-sm'
          : 'border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary hover:border-[var(--border-strong)] hover:text-primary'
      }`}
    >
      <span className="block break-words">{children}</span>
    </button>
  )
}

export default function FilterModal({ config, filter, onClose, onSaved }: FilterModalProps) {
  const isEdit = filter !== null
  const [form, setForm] = useState<FilterFormData>(() => buildInitialForm(filter, config))
  const [saving, setSaving] = useState(false)
  const [keywordsOpen, setKeywordsOpen] = useState(true)
  const [excludeOpen, setExcludeOpen] = useState(false)
  const [keywordSearch, setKeywordSearch] = useState('')
  const [customKeyword, setCustomKeyword] = useState('')

  useEffect(() => {
    const onEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onEscape)
    return () => document.removeEventListener('keydown', onEscape)
  }, [onClose])

  const siteKeys = useMemo(() => Object.keys(config.sites), [config.sites])
  const selectedSalary = config.salaries.find((s) => s[2] === form.salary_min && s[3] === form.salary_max)
  const salaryKey = selectedSalary ? selectedSalary[0] : 'any'
  const searchTerm = keywordSearch.trim().toLowerCase()

  const visibleKeywordGroups = useMemo(() => {
    if (!searchTerm) return Object.entries(config.keyword_groups)
    return Object.entries(config.keyword_groups)
      .map(([group, items]) => {
        const filteredItems = Object.fromEntries(
          Object.entries(items).filter(([keyword, synonyms]) => {
            const haystack = [group, keyword, ...synonyms].join(' ').toLowerCase()
            return haystack.includes(searchTerm)
          }),
        )
        return [group, filteredItems] as const
      })
      .filter(([, items]) => Object.keys(items).length > 0)
  }, [config.keyword_groups, searchTerm])

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

  const addGroupKeywords = (items: Record<string, string[]>) => {
    setForm((prev) => ({ ...prev, keywords: unique([...prev.keywords, ...Object.keys(items)]) }))
  }

  const removeGroupKeywords = (items: Record<string, string[]>) => {
    const groupKeywords = new Set(Object.keys(items))
    setForm((prev) => ({ ...prev, keywords: prev.keywords.filter((kw) => !groupKeywords.has(kw)) }))
  }

  const addCustomKeyword = () => {
    const value = customKeyword.trim()
    if (!value) return
    setForm((prev) => ({
      ...prev,
      name: prev.name.trim() ? prev.name : value,
      keywords: prev.keywords.includes(value) ? prev.keywords : [...prev.keywords, value],
    }))
    setCustomKeyword('')
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
    const autoName = buildAutoName(form, config)
    const payload = {
      ...form,
      name: form.name.trim() || autoName,
      keywords: unique(form.keywords),
      exclude_keywords: unique(form.exclude_keywords),
      sites: unique(form.sites),
    }

    if (payload.keywords.length === 0) {
      toast.error('Выберите ключевые слова или добавьте свой запрос')
      return
    }
    if (payload.sites.length === 0) {
      toast.error('Выберите хотя бы один источник')
      return
    }

    setSaving(true)
    try {
      let saved: VacancyFilter
      if (isEdit && filter) {
        saved = (await api.updateFilter(filter.id, payload)).filter
        toast.success('Фильтр обновлён')
      } else {
        saved = (await api.createFilter(payload)).filter
        toast.success('Фильтр создан')
      }
      onSaved(saved)
      onClose()
    } catch {
      toast.error('Не удалось сохранить фильтр')
    } finally {
      setSaving(false)
    }
  }

  const selectedCity = form.city ? config.cities[form.city] || form.city : 'Любой город'
  const selectedExperience = form.experience ? config.experiences[form.experience] || form.experience : 'Любой опыт'
  const selectedEmployment = form.employment_types.length
    ? form.employment_types.map((item) => config.employment_types[item] || item).join(', ')
    : 'Любой формат'

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
      <div className="animate-soft-scale flex h-[94vh] w-full max-w-5xl flex-col rounded-t-3xl border border-[var(--border)] bg-[color:var(--surface-strong)] shadow-[var(--shadow-lg)] md:h-auto md:max-h-[92vh] md:rounded-2xl">
        <header className="sticky top-0 z-10 flex items-center justify-between border-b border-[var(--border)] bg-[color:var(--surface)]/92 px-4 py-3 backdrop-blur md:px-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Конструктор фильтра</p>
            <h2 className="text-base font-semibold text-primary md:text-lg">
              {isEdit ? 'Редактирование фильтра' : 'Новый фильтр поиска'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary transition hover:text-primary"
            aria-label="Закрыть"
          >
            <X className="h-4 w-4" />
          </button>
        </header>

        <div className="grid flex-1 gap-4 overflow-y-auto px-4 py-4 md:grid-cols-[minmax(0,1fr)_290px] md:px-6 md:py-5">
          <div className="space-y-4">
            <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Название фильтра</label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                placeholder={buildAutoName(form, config)}
                className="focus-ring mt-2 h-11 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary placeholder:text-muted"
              />
              <p className="mt-2 text-xs text-secondary">
                Можно оставить пустым — название соберётся автоматически по ключевым словам, городу и зарплате.
              </p>
            </section>

            <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <button
                type="button"
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
                  <div className="grid gap-2 md:grid-cols-[minmax(0,1fr)_220px]">
                    <label className="focus-within:focus-ring flex h-11 items-center gap-2 rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-secondary">
                      <Search className="h-4 w-4 shrink-0" />
                      <input
                        value={keywordSearch}
                        onChange={(e) => setKeywordSearch(e.target.value)}
                        placeholder="Найти роль или технологию"
                        className="min-w-0 flex-1 bg-transparent text-primary outline-none placeholder:text-muted"
                      />
                    </label>
                    <div className="flex gap-2">
                      <input
                        value={customKeyword}
                        onChange={(e) => setCustomKeyword(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            e.preventDefault()
                            addCustomKeyword()
                          }
                        }}
                        placeholder="Свой запрос"
                        className="focus-ring h-11 min-w-0 flex-1 rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary placeholder:text-muted"
                      />
                      <button
                        type="button"
                        onClick={addCustomKeyword}
                        className="focus-ring h-11 shrink-0 rounded-xl bg-[var(--accent)] px-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
                      >
                        Добавить
                      </button>
                    </div>
                  </div>

                  {visibleKeywordGroups.length === 0 ? (
                    <div className="rounded-xl border border-dashed border-[var(--border)] p-4 text-sm text-secondary">
                      Ничего не найдено. Добавь свой запрос вручную выше.
                    </div>
                  ) : (
                    visibleKeywordGroups.map(([group, items]) => (
                      <div key={group} className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] p-3">
                        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                          <p className="text-xs font-semibold text-secondary">{group}</p>
                          <div className="flex gap-2 text-[11px] font-semibold">
                            <button type="button" onClick={() => addGroupKeywords(items)} className="text-[var(--accent)] hover:underline">Выбрать группу</button>
                            <button type="button" onClick={() => removeGroupKeywords(items)} className="text-muted hover:text-secondary">Снять</button>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {Object.keys(items).map((kw) => (
                            <ToggleChip key={kw} selected={form.keywords.includes(kw)} onClick={() => toggleKeyword(kw)}>
                              {kw}
                            </ToggleChip>
                          ))}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </section>

            <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <button
                type="button"
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
                  {visibleKeywordGroups.map(([group, items]) => (
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
              <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Город</label>
                <select
                  value={form.city ?? ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value || null }))}
                  className="focus-ring mt-2 h-11 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
                >
                  <option value="">Любой</option>
                  {Object.entries(config.cities).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </section>

              <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Зарплата</label>
                <select
                  value={salaryKey}
                  onChange={(e) => handleSalaryChange(e.target.value)}
                  className="focus-ring mt-2 h-11 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
                >
                  {config.salaries.map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </section>
            </div>

            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Тип занятости</label>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {Object.entries(config.employment_types).map(([key, label]) => (
                    <ToggleChip key={key} selected={form.employment_types.includes(key)} onClick={() => toggleEmployment(key)}>
                      {label}
                    </ToggleChip>
                  ))}
                </div>
              </section>

              <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Опыт</label>
                <select
                  value={form.experience ?? ''}
                  onChange={(e) => setForm((prev) => ({ ...prev, experience: e.target.value || null }))}
                  className="focus-ring mt-2 h-11 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3 text-sm text-primary"
                >
                  <option value="">Любой</option>
                  {Object.entries(config.experiences).map(([key, label]) => (
                    <option key={key} value={key}>{label}</option>
                  ))}
                </select>
              </section>
            </div>

            <section className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <label className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Источники ({form.sites.length})</label>
                <div className="flex gap-2 text-xs font-semibold">
                  <button type="button" onClick={() => setForm((prev) => ({ ...prev, sites: siteKeys }))} className="text-[var(--accent)] hover:underline">Все</button>
                  <button type="button" onClick={() => setForm((prev) => ({ ...prev, sites: [] }))} className="text-muted hover:text-secondary">Снять</button>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {Object.entries(config.sites).map(([key, label]) => (
                  <ToggleChip key={key} selected={form.sites.includes(key)} onClick={() => toggleSite(key)}>
                    {label}
                  </ToggleChip>
                ))}
              </div>
            </section>
          </div>

          <aside className="h-fit rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4 md:sticky md:top-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Сводка</p>
            <div className="mt-3 space-y-3 text-sm">
              <div>
                <p className="text-xs text-muted">Запросы</p>
                <p className="mt-1 text-primary">{form.keywords.length ? form.keywords.slice(0, 4).join(', ') : 'Пока не выбраны'}</p>
                {form.keywords.length > 4 && <p className="text-xs text-muted">+ ещё {form.keywords.length - 4}</p>}
              </div>
              <div>
                <p className="text-xs text-muted">География и опыт</p>
                <p className="mt-1 text-primary">{selectedCity} · {selectedExperience}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Формат</p>
                <p className="mt-1 text-primary">{selectedEmployment}</p>
              </div>
              <div>
                <p className="text-xs text-muted">Источники</p>
                <p className="mt-1 text-primary">{form.sites.length === siteKeys.length ? 'Все 5 сайтов' : `${form.sites.length} из ${siteKeys.length}`}</p>
              </div>
            </div>
            <div className="mt-4 rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] p-3 text-xs leading-relaxed text-secondary">
              Совет: если выдача пустая, сначала оставь город, опыт и занятость как “любой”, проверь результат, а потом сужай фильтр.
            </div>
          </aside>
        </div>

        <footer className="sticky bottom-0 grid grid-cols-2 gap-2 border-t border-[var(--border)] bg-[color:var(--surface)]/95 px-4 py-3 backdrop-blur md:flex md:justify-end md:px-6">
          <button
            type="button"
            onClick={onClose}
            className="focus-ring h-11 min-w-0 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-4 text-sm font-semibold text-secondary transition hover:text-primary"
          >
            Отмена
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="focus-ring h-11 min-w-0 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="block truncate">{saving ? 'Сохранение...' : isEdit ? 'Сохранить' : 'Создать фильтр'}</span>
          </button>
        </footer>
      </div>
    </div>
  )
}

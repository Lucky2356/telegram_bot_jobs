import { useState, useEffect, useCallback } from 'react'
import type { AppConfig, FilterFormData, VacancyFilter } from '../types'
import { api } from '../api'
import { toast } from './Toast'

interface FilterModalProps {
  config: AppConfig
  filter: VacancyFilter | null
  onClose: () => void
  onSaved: () => void
}

export default function FilterModal({ config, filter, onClose, onSaved }: FilterModalProps) {
  const isEdit = filter !== null
  const [form, setForm] = useState<FilterFormData>({
    name: '', keywords: [], city: null,
    salary_min: null, salary_max: null,
    employment_types: [], sites: [],
    exclude_keywords: [], experience: null,
  })
  const [saving, setSaving] = useState(false)
  const [kwCollapsed, setKwCollapsed] = useState(false)
  const [exCollapsed, setExCollapsed] = useState(true)

  useEffect(() => {
    if (filter) {
      setForm({
        name: filter.name, keywords: filter.keywords, city: filter.city,
        salary_min: filter.salary_min, salary_max: filter.salary_max,
        employment_types: filter.employment_types, sites: filter.sites,
        exclude_keywords: filter.exclude_keywords, experience: filter.experience,
      })
    }
  }, [filter])

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handleKey)
    return () => document.removeEventListener('keydown', handleKey)
  }, [onClose])

  const toggleKeyword = (kw: string) => {
    setForm((prev) => ({
      ...prev,
      keywords: prev.keywords.includes(kw)
        ? prev.keywords.filter((k) => k !== kw)
        : [...prev.keywords, kw],
    }))
  }

  const toggleExclude = (kw: string) => {
    setForm((prev) => ({
      ...prev,
      exclude_keywords: prev.exclude_keywords.includes(kw)
        ? prev.exclude_keywords.filter((k) => k !== kw)
        : [...prev.exclude_keywords, kw],
    }))
  }

  const toggleEmployment = (key: string) => {
    setForm((prev) => ({
      ...prev,
      employment_types: prev.employment_types.includes(key)
        ? prev.employment_types.filter((e) => e !== key)
        : [...prev.employment_types, key],
    }))
  }

  const toggleSite = (key: string) => {
    setForm((prev) => ({
      ...prev,
      sites: prev.sites.includes(key)
        ? prev.sites.filter((s) => s !== key)
        : [...prev.sites, key],
    }))
  }

  const handleSave = async () => {
    if (!form.name.trim()) { toast.error('Введите название фильтра'); return }
    if (form.keywords.length === 0) { toast.error('Выберите хотя бы одно ключевое слово'); return }
    if (form.sites.length === 0) { toast.error('Выберите хотя бы один сайт'); return }
    setSaving(true)
    try {
      if (isEdit) {
        await api.updateFilter(filter.id, form)
        toast.success('Фильтр обновлён')
      } else {
        await api.createFilter(form)
        toast.success('Фильтр создан')
      }
      onSaved(); onClose()
    } catch { toast.error('Ошибка сохранения') }
    finally { setSaving(false) }
  }

  const selectedSalary = config.salaries.find(
    (s) => s[2] === form.salary_min && s[3] === form.salary_max,
  )
  const salaryKey = selectedSalary ? selectedSalary[0] : 'any'

  const handleSalaryChange = (key: string) => {
    if (key === 'any') { setForm((prev) => ({ ...prev, salary_min: null, salary_max: null })); return }
    const salary = config.salaries.find((s) => s[0] === key)
    if (salary) setForm((prev) => ({ ...prev, salary_min: salary[2], salary_max: salary[3] }))
  }

  const overlayRef = useCallback((node: HTMLDivElement | null) => {
    if (node) {
      node.addEventListener('click', (e) => { if (e.target === node) onClose() })
    }
  }, [onClose])

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-label={isEdit ? 'Редактировать фильтр' : 'Создать фильтр'}
      aria-modal="true"
    >
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 z-10 flex items-center justify-between px-6 pt-5 pb-3 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            {isEdit ? '✏️ Редактировать фильтр' : '➕ Создать фильтр'}
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-5">

          {/* Name */}
          <div>
            <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
              📛 Название
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full px-3.5 py-2.5 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
              placeholder="Мой фильтр"
            />
          </div>

          {/* Keywords */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setKwCollapsed(!kwCollapsed)}
              className="flex items-center justify-between w-full text-left cursor-pointer"
              aria-label={kwCollapsed ? 'Развернуть' : 'Свернуть'}
            >
              <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                🔑 Ключевые слова
                <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-primary/10 text-primary font-medium">
                  {form.keywords.length}
                </span>
              </span>
              <span className="text-gray-400 text-sm">{kwCollapsed ? '▶' : '▼'}</span>
            </button>

            {!kwCollapsed && (
              <div className="mt-3 space-y-3">
                {/* Selected chips */}
                {form.keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {form.keywords.map((kw) => (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-primary text-white" key={kw}>
                        {kw}
                        <button
                          onClick={() => toggleKeyword(kw)}
                          className="ml-0.5 hover:text-white/70 cursor-pointer"
                          aria-label={`Убрать ${kw}`}
                        >
                          ✕
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Groups */}
                {Object.entries(config.keyword_groups).map(([group, items]) => {
                  const groupKws = Object.keys(items)
                  const selectedCount = groupKws.filter((kw) => form.keywords.includes(kw)).length
                  return (
                    <div key={group}>
                      <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 mb-1.5">
                        {group}
                        <span className="ml-1 font-normal text-gray-300 dark:text-gray-600">
                          {selectedCount}/{groupKws.length}
                        </span>
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {groupKws.map((kw) => {
                          const sel = form.keywords.includes(kw)
                          return (
                            <button
                              key={kw}
                              onClick={() => toggleKeyword(kw)}
                              className={`px-2.5 py-1 text-xs rounded-lg border transition-all cursor-pointer ${
                                sel
                                  ? 'bg-primary text-white border-primary shadow-sm'
                                  : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-primary hover:text-primary'
                              }`}
                              aria-label={sel ? `Убрать ${kw}` : `Добавить ${kw}`}
                            >
                              {kw}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {/* Exclude keywords */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-4 border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setExCollapsed(!exCollapsed)}
              className="flex items-center justify-between w-full text-left cursor-pointer"
            >
              <span className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                🚫 Исключить
                {form.exclude_keywords.length > 0 && (
                  <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-red-100 dark:bg-red-900/30 text-red-500 font-medium">
                    {form.exclude_keywords.length}
                  </span>
                )}
              </span>
              <span className="text-gray-400 text-sm">{exCollapsed ? '▶' : '▼'}</span>
            </button>

            {!exCollapsed && (
              <div className="mt-3 space-y-3">
                {form.exclude_keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {form.exclude_keywords.map((kw) => (
                      <span className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full bg-red-500 text-white" key={`ex-chip-${kw}`}>
                        {kw}
                        <button
                          onClick={() => toggleExclude(kw)}
                          className="ml-0.5 hover:text-white/70 cursor-pointer"
                          aria-label={`Не исключать ${kw}`}
                        >
                          ✕
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {Object.values(config.keyword_groups).map((items) =>
                  Object.keys(items).map((kw) => {
                    const sel = form.exclude_keywords.includes(kw)
                    return (
                      <button
                        key={`ex-${kw}`}
                        onClick={() => toggleExclude(kw)}
                        className={`px-2.5 py-1 text-xs rounded-lg border transition-all cursor-pointer mr-1 mb-1 ${
                          sel
                            ? 'bg-red-500 text-white border-red-500 shadow-sm'
                            : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-red-400 hover:text-red-500'
                        }`}
                        aria-label={sel ? `Не исключать ${kw}` : `Исключить ${kw}`}
                      >
                        {kw}
                      </button>
                    )
                  }),
                )}
              </div>
            )}
          </div>

          {/* City + Salary */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3.5 border border-gray-200 dark:border-gray-700">
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                📍 Город
              </label>
              <select
                value={form.city ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value || null }))}
                className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">🌍 Любой</option>
                {Object.entries(config.cities).map(([key, label]) => (
                  <option key={key} value={key}>📍 {label}</option>
                ))}
              </select>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3.5 border border-gray-200 dark:border-gray-700">
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                💰 Зарплата
              </label>
              <select
                value={salaryKey}
                onChange={(e) => handleSalaryChange(e.target.value)}
                className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {config.salaries.map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Employment + Experience */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3.5 border border-gray-200 dark:border-gray-700">
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                👔 Тип занятости
              </label>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(config.employment_types).map(([key, label]) => {
                  const sel = form.employment_types.includes(key)
                  return (
                    <button
                      key={key}
                      onClick={() => toggleEmployment(key)}
                      className={`px-2.5 py-1 text-xs rounded-lg border transition-all cursor-pointer ${
                        sel
                          ? 'bg-primary text-white border-primary shadow-sm'
                          : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-primary'
                      }`}
                      aria-label={sel ? `Убрать ${label}` : `Выбрать ${label}`}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3.5 border border-gray-200 dark:border-gray-700">
              <label className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                💼 Опыт
              </label>
              <select
                value={form.experience ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, experience: e.target.value || null }))}
                className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Любой</option>
                {Object.entries(config.experiences).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Sites */}
          <div className="bg-gray-50 dark:bg-gray-900 rounded-xl p-3.5 border border-gray-200 dark:border-gray-700">
            <label className="flex items-center gap-1.5 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
              🌐 Сайты
              <span className="ml-1.5 px-1.5 py-0.5 text-[10px] rounded-full bg-primary/10 text-primary font-medium">
                {form.sites.length}
              </span>
            </label>
            <div className="flex flex-wrap gap-1.5">
              {Object.entries(config.sites).map(([key, label]) => {
                const sel = form.sites.includes(key)
                return (
                  <button
                    key={key}
                    onClick={() => toggleSite(key)}
                    className={`px-3 py-1.5 text-sm rounded-lg border transition-all cursor-pointer ${
                      sel
                        ? 'bg-primary text-white border-primary shadow-sm'
                        : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:border-primary'
                    }`}
                    aria-label={sel ? `Убрать ${label}` : `Выбрать ${label}`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-gray-800 flex items-center justify-end gap-2 px-6 py-4 border-t border-gray-100 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer transition-all"
          >
            Отмена
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-5 py-2 text-sm font-medium bg-primary text-white rounded-xl hover:bg-primary-hover disabled:opacity-50 transition-all cursor-pointer shadow-sm"
          >
            {saving ? '⏳ Сохранение...' : isEdit ? '💾 Сохранить' : '✅ Создать фильтр'}
          </button>
        </div>
      </div>
    </div>
  )
}

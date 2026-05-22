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
    name: '',
    keywords: [],
    city: null,
    salary_min: null,
    salary_max: null,
    employment_types: [],
    sites: [],
    exclude_keywords: [],
    experience: null,
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (filter) {
      setForm({
        name: filter.name,
        keywords: filter.keywords,
        city: filter.city,
        salary_min: filter.salary_min,
        salary_max: filter.salary_max,
        employment_types: filter.employment_types,
        sites: filter.sites,
        exclude_keywords: filter.exclude_keywords,
        experience: filter.experience,
      })
    }
  }, [filter])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown as unknown as EventListener)
    return () => document.removeEventListener('keydown', handleKeyDown as unknown as EventListener)
  }, [handleKeyDown])

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
    if (!form.name.trim()) {
      toast.error('Введите название фильтра')
      return
    }
    if (form.keywords.length === 0) {
      toast.error('Выберите хотя бы одно ключевое слово')
      return
    }
    if (form.sites.length === 0) {
      toast.error('Выберите хотя бы один сайт')
      return
    }

    setSaving(true)
    try {
      if (isEdit) {
        await api.updateFilter(filter.id, form)
        toast.success('Фильтр обновлён')
      } else {
        await api.createFilter(form)
        toast.success('Фильтр создан')
      }
      onSaved()
      onClose()
    } catch {
      toast.error('Ошибка сохранения фильтра')
    } finally {
      setSaving(false)
    }
  }

  const selectedSalary = config.salaries.find(
    (s) => s[2] === form.salary_min && s[3] === form.salary_max,
  )
  const salaryKey = selectedSalary ? selectedSalary[0] : 'any'

  const handleSalaryChange = (key: string) => {
    if (key === 'any') {
      setForm((prev) => ({ ...prev, salary_min: null, salary_max: null }))
      return
    }
    const salary = config.salaries.find((s) => s[0] === key)
    if (salary) {
      setForm((prev) => ({ ...prev, salary_min: salary[2], salary_max: salary[3] }))
    }
  }

  const overlayRef = useCallback((node: HTMLDivElement | null) => {
    if (node) {
      const handleClick = (e: MouseEvent) => {
        if (e.target === node) onClose()
      }
      node.addEventListener('click', handleClick)
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
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">
            {isEdit ? '✏️ Редактировать фильтр' : '➕ Создать фильтр'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 cursor-pointer"
            aria-label="Закрыть"
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClose() } }}
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Название
            </label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Мой фильтр"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Ключевые слова
            </label>
            <div className="max-h-48 overflow-y-auto space-y-2 border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              {Object.entries(config.keyword_groups).map(([group, items]) => (
                <div key={group}>
                  <p className="text-xs font-semibold text-gray-400 uppercase mb-1">{group}</p>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(items).map((kw) => {
                      const selected = form.keywords.includes(kw)
                      return (
                        <button
                          key={kw}
                          onClick={() => toggleKeyword(kw)}
                          className={`px-2 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                            selected
                              ? 'bg-primary text-white border-primary'
                              : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary'
                          }`}
                          aria-label={`${selected ? 'Убрать' : 'Добавить'} ключевое слово ${kw}`}
                        >
                          {kw}
                        </button>
                      )
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Исключить слова
            </label>
            <div className="flex flex-wrap gap-1 max-h-32 overflow-y-auto border border-gray-200 dark:border-gray-700 rounded-lg p-3">
              {Object.values(config.keyword_groups).map((items) =>
                Object.keys(items).map((kw) => {
                  const selected = form.exclude_keywords.includes(kw)
                  return (
                    <button
                      key={`ex-${kw}`}
                      onClick={() => toggleExclude(kw)}
                      className={`px-2 py-1 text-xs rounded-full border transition-colors cursor-pointer ${
                        selected
                          ? 'bg-red-500 text-white border-red-500'
                          : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-red-400'
                      }`}
                      aria-label={selected ? `Не исключать ${kw}` : `Исключить ${kw}`}
                    >
                      {kw}
                    </button>
                  )
                }),
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Город
              </label>
              <select
                value={form.city ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, city: e.target.value || null }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Любой</option>
                {Object.entries(config.cities).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Зарплата
              </label>
              <select
                value={salaryKey}
                onChange={(e) => handleSalaryChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {config.salaries.map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Тип занятости
              </label>
              <div className="flex flex-wrap gap-1 border border-gray-200 dark:border-gray-700 rounded-lg p-2">
                {Object.entries(config.employment_types).map(([key, label]) => {
                  const selected = form.employment_types.includes(key)
                  return (
                    <button
                      key={key}
                      onClick={() => toggleEmployment(key)}
                      className={`px-2 py-1 text-xs rounded transition-colors cursor-pointer ${
                        selected
                          ? 'bg-primary text-white'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                      }`}
                      aria-label={selected ? `Убрать ${label}` : `Выбрать ${label}`}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
                Опыт
              </label>
              <select
                value={form.experience ?? ''}
                onChange={(e) => setForm((prev) => ({ ...prev, experience: e.target.value || null }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">Любой</option>
                {Object.entries(config.experiences).map(([key, label]) => (
                  <option key={key} value={key}>{label}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">
              Сайты
            </label>
            <div className="flex flex-wrap gap-1">
              {Object.entries(config.sites).map(([key, label]) => {
                const selected = form.sites.includes(key)
                return (
                  <button
                    key={key}
                    onClick={() => toggleSite(key)}
                    className={`px-3 py-1.5 text-sm rounded-lg border transition-colors cursor-pointer ${
                      selected
                        ? 'bg-primary text-white border-primary'
                        : 'border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-primary'
                    }`}
                    aria-label={selected ? `Убрать ${label}` : `Выбрать ${label}`}
                  >
                    {label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 cursor-pointer"
            aria-label="Отмена"
          >
            Отмена
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 cursor-pointer"
            aria-label={isEdit ? 'Сохранить фильтр' : 'Создать фильтр'}
          >
            {saving ? 'Сохранение...' : isEdit ? '💾 Сохранить' : '✅ Создать'}
          </button>
        </div>
      </div>
    </div>
  )
}

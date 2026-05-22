import { useState } from 'react'
import type { VacancyFilter, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import FilterModal from './FilterModal'

interface FiltersPanelProps {
  filters: VacancyFilter[]
  config: AppConfig
  onRefresh: () => void
}

export default function FiltersPanel({ filters, config, onRefresh }: FiltersPanelProps) {
  const [editFilter, setEditFilter] = useState<VacancyFilter | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editingNameId, setEditingNameId] = useState<number | null>(null)
  const [editingNameValue, setEditingNameValue] = useState('')

  const handleToggle = async (id: number) => {
    try {
      await api.toggleFilter(id)
      onRefresh()
    } catch {
      toast.error('Ошибка переключения фильтра')
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Удалить фильтр?')) return
    try {
      await api.deleteFilter(id)
      toast.success('Фильтр удалён')
      onRefresh()
    } catch {
      toast.error('Ошибка удаления')
    }
  }

  const startNameEdit = (filter: VacancyFilter) => {
    setEditingNameId(filter.id)
    setEditingNameValue(filter.name)
  }

  const saveNameEdit = async (id: number) => {
    if (!editingNameValue.trim()) {
      setEditingNameId(null)
      return
    }
    try {
      const f = filters.find((x) => x.id === id)
      if (!f) return
      await api.updateFilter(id, {
        name: editingNameValue,
        keywords: f.keywords,
        city: f.city,
        salary_min: f.salary_min,
        salary_max: f.salary_max,
        employment_types: f.employment_types,
        sites: f.sites,
        exclude_keywords: f.exclude_keywords,
        experience: f.experience,
      })
      toast.success('Название обновлено')
      setEditingNameId(null)
      onRefresh()
    } catch {
      toast.error('Ошибка обновления')
      setEditingNameId(null)
    }
  }

  if (filters.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <p className="text-lg mb-2">Фильтров пока нет</p>
        <p className="text-sm">Создайте в Telegram через /add_filter или нажмите кнопку выше</p>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table" aria-label="Список фильтров">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 text-xs uppercase">
              <th className="text-left py-3 px-2 font-medium">Название</th>
              <th className="text-left py-3 px-2 font-medium">Ключевые слова</th>
              <th className="text-left py-3 px-2 font-medium hidden md:table-cell">Город</th>
              <th className="text-left py-3 px-2 font-medium hidden md:table-cell">Зарплата</th>
              <th className="text-left py-3 px-2 font-medium hidden lg:table-cell">Сайты</th>
              <th className="text-center py-3 px-2 font-medium">Статус</th>
              <th className="text-right py-3 px-2 font-medium">Действия</th>
            </tr>
          </thead>
          <tbody>
            {filters.map((f) => (
              <tr
                key={f.id}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <td className="py-3 px-2">
                  {editingNameId === f.id ? (
                    <input
                      type="text"
                      value={editingNameValue}
                      onChange={(e) => setEditingNameValue(e.target.value)}
                      onBlur={() => saveNameEdit(f.id)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveNameEdit(f.id)
                        if (e.key === 'Escape') setEditingNameId(null)
                      }}
                      className="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 text-sm w-full focus:outline-none focus:ring-2 focus:ring-primary"
                      autoFocus
                      aria-label="Название фильтра"
                    />
                  ) : (
                    <button
                      onClick={() => startNameEdit(f)}
                      className="font-medium text-gray-900 dark:text-gray-100 hover:text-primary cursor-pointer"
                      aria-label={`Редактировать название фильтра ${f.name}`}
                      tabIndex={0}
                      onKeyDown={(e) => { if (e.key === 'Enter') startNameEdit(f) }}
                    >
                      {f.name}
                    </button>
                  )}
                </td>
                <td className="py-3 px-2">
                  <div className="flex flex-wrap gap-1">
                    {f.keywords.map((kw) => (
                      <span
                        key={kw}
                        className="px-2 py-0.5 text-xs rounded-full bg-primary-light dark:bg-primary/20 text-primary dark:text-primary-light"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400 hidden md:table-cell">
                  {f.city || 'Любой'}
                </td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400 hidden md:table-cell">
                  {f.salary_min != null || f.salary_max != null
                    ? `${f.salary_min ? `от ${f.salary_min.toLocaleString()}` : ''} ${f.salary_max ? `до ${f.salary_max.toLocaleString()}` : ''} ₽`
                    : 'Любая'}
                </td>
                <td className="py-3 px-2 hidden lg:table-cell">
                  <div className="flex flex-wrap gap-1">
                    {f.sites.map((s) => (
                      <span key={s} className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                        {config.sites[s] || s}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="py-3 px-2 text-center">
                  <button
                    onClick={() => handleToggle(f.id)}
                    className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors cursor-pointer ${
                      f.active ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                    role="switch"
                    aria-checked={f.active}
                    aria-label={`Фильтр ${f.name}: ${f.active ? 'активен' : 'на паузе'}`}
                    tabIndex={0}
                    onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); handleToggle(f.id) }}}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        f.active ? 'translate-x-4.5' : 'translate-x-0.5'
                      }`}
                    />
                  </button>
                </td>
                <td className="py-3 px-2 text-right">
                  <div className="flex gap-1 justify-end">
                    <button
                      onClick={() => setEditFilter(f)}
                      className="px-2 py-1 text-xs text-gray-500 hover:text-primary dark:text-gray-400 dark:hover:text-primary cursor-pointer"
                      aria-label={`Редактировать фильтр ${f.name}`}
                    >
                      ✏️
                    </button>
                    <button
                      onClick={() => handleDelete(f.id)}
                      className="px-2 py-1 text-xs text-gray-500 hover:text-red-500 dark:text-gray-400 dark:hover:text-red-400 cursor-pointer"
                      aria-label={`Удалить фильтр ${f.name}`}
                    >
                      🗑
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editFilter && (
        <FilterModal
          config={config}
          filter={editFilter}
          onClose={() => setEditFilter(null)}
          onSaved={onRefresh}
        />
      )}

      {createOpen && (
        <FilterModal
          config={config}
          filter={null}
          onClose={() => setCreateOpen(false)}
          onSaved={onRefresh}
        />
      )}
    </>
  )
}

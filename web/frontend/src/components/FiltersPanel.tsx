import { useState } from 'react'
import type { VacancyFilter, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import FilterModal from './FilterModal'

interface FiltersPanelProps {
  filters: VacancyFilter[]
  config: AppConfig
  selectedId: number | null
  onSelect: (id: number | null) => void
  onRefresh: () => void
}

export default function FiltersPanel({ filters, config, selectedId, onSelect, onRefresh }: FiltersPanelProps) {
  const [editFilter, setEditFilter] = useState<VacancyFilter | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null)

  const handleToggle = async (id: number) => {
    try {
      const res = await api.toggleFilter(id)
      toast.success(res.active ? 'Фильтр включён' : 'Фильтр на паузе')
      onRefresh()
    } catch {
      toast.error('Ошибка')
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deleteFilter(id)
      toast.success('Фильтр удалён')
      if (selectedId === id) onSelect(null)
      onRefresh()
    } catch {
      toast.error('Ошибка удаления')
    }
  }

  if (filters.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 dark:text-gray-400">
        <p className="text-base mb-1">Фильтров пока нет</p>
        <p className="text-sm">Создайте в Telegram через /add_filter</p>
      </div>
    )
  }

  return (
    <>
      {/* Active filter chips row */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => onSelect(null)}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
            selectedId === null
              ? 'bg-primary text-white border-primary shadow-sm'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-primary'
          }`}
          aria-label="Показать все фильтры"
        >
          Все фильтры
        </button>
        {filters.map((f) => (
          <div
            key={f.id}
            className={`group relative flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
              selectedId === f.id
                ? 'bg-primary text-white border-primary shadow-sm'
                : f.active
                  ? 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-primary'
                  : 'bg-gray-50 dark:bg-gray-800/50 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-700 hover:border-gray-400'
            }`}
            onClick={() => onSelect(f.id)}
            role="tab"
            aria-selected={selectedId === f.id}
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(f.id) }}}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${f.active ? 'bg-emerald-400' : 'bg-gray-300 dark:bg-gray-600'}`} />
            <span className={!f.active ? 'line-through' : ''}>{f.name}</span>
            <span className="text-[10px] opacity-60 ml-0.5">
              {f.keywords.length} кл.
            </span>
            {/* Quick actions on hover */}
            <div className="hidden group-hover:flex absolute -top-2 -right-2 gap-0.5">
              <button
                onClick={(e) => { e.stopPropagation(); handleToggle(f.id) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-500 hover:text-primary cursor-pointer shadow-sm"
                aria-label={f.active ? 'Выключить' : 'Включить'}
              >
                {f.active ? '⏸' : '▶️'}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setEditFilter(f) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded-full bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 text-gray-500 hover:text-primary cursor-pointer shadow-sm"
                aria-label="Редактировать"
              >
                ✏️
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Confirm delete */}
      {confirmDeleteId && (
        <div className="flex items-center gap-2 mb-3 p-3 bg-red-50 dark:bg-red-900/10 rounded-lg border border-red-200 dark:border-red-800">
          <span className="text-sm text-red-700 dark:text-red-300">Удалить фильтр?</span>
          <button
            onClick={() => { handleDelete(confirmDeleteId); setConfirmDeleteId(null) }}
            className="px-3 py-1 text-xs font-medium bg-red-500 text-white rounded-lg hover:bg-red-600 cursor-pointer"
          >
            Да, удалить
          </button>
          <button
            onClick={() => setConfirmDeleteId(null)}
            className="px-3 py-1 text-xs text-gray-500 hover:text-gray-700 cursor-pointer"
          >
            Отмена
          </button>
        </div>
      )}

      {editFilter && (
        <FilterModal config={config} filter={editFilter} onClose={() => setEditFilter(null)} onSaved={onRefresh} />
      )}
      {createOpen && (
        <FilterModal config={config} filter={null} onClose={() => setCreateOpen(false)} onSaved={onRefresh} />
      )}
    </>
  )
}

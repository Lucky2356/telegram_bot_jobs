import { useState, useMemo } from 'react'
import type { VacancyFilter, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import FilterModal from './FilterModal'
import ConfirmModal from './ConfirmModal'

interface FiltersPanelProps {
  filters: VacancyFilter[]
  config: AppConfig
  selectedId: number | null
  onSelect: (id: number | null) => void
  onRefresh: () => void
}

export default function FiltersPanel({ filters, config, selectedId, onSelect, onRefresh }: FiltersPanelProps) {
  const [editFilter, setEditFilter] = useState<VacancyFilter | null>(null)
  const [checkingId, setCheckingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const filtered = useMemo(
    () => search ? filters.filter((f) => f.name.toLowerCase().includes(search.toLowerCase())) : filters,
    [filters, search],
  )

  const handleToggle = async (id: number) => {
    try {
      const res = await api.toggleFilter(id)
      toast.success(res.active ? 'Фильтр включён' : 'Фильтр на паузе')
      onRefresh()
    } catch { toast.error('Ошибка') }
  }

  const handleCheckOne = async (id: number) => {
    setCheckingId(id)
    try {
      await api.checkFilter(id)
      toast.success('Проверка запущена!')
      setTimeout(() => onRefresh(), 2000)
    } catch { toast.error('Ошибка') }
    finally { setCheckingId(null) }
  }

  const handleClone = async (id: number) => {
    try {
      await api.cloneFilter(id)
      toast.success('Фильтр склонирован')
      onRefresh()
    } catch {
      toast.error('Ошибка клонирования')
    }
  }

  if (filters.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 dark:text-slate-500">
        <p className="text-sm">Фильтров пока нет</p>
      </div>
    )
  }

  return (
    <>
      {(filters.length > 5 || true) && (
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск фильтров..."
          className="w-full mb-2 h-9 px-3 text-xs border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
          aria-label="Поиск фильтров"
        />
      )}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onSelect(null)}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
            selectedId === null
              ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-950 dark:border-white shadow-sm'
              : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-700 hover:border-slate-400'
          }`}
        >
          Все
        </button>
        {filtered.map((f) => (
          <div
            key={f.id}
            className={`group relative flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
              selectedId === f.id
                ? 'bg-slate-900 text-white border-slate-900 dark:bg-white dark:text-slate-950 dark:border-white shadow-sm'
                : f.active
                  ? 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 border-slate-200 dark:border-slate-700 hover:border-slate-400'
                  : 'bg-slate-50 dark:bg-slate-800/30 text-slate-400 dark:text-slate-500 border-slate-200 dark:border-slate-700'
            }`}
            onClick={() => onSelect(f.id)}
            role="tab"
            aria-selected={selectedId === f.id}
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(f.id) }}}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${f.active ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`} />
            <span className={`${!f.active ? 'line-through' : ''} max-w-[120px] truncate`}>{f.name}</span>

            <div className="flex md:group-hover:flex items-center gap-0.5 ml-1 shrink-0">
              {f.active && (
                <button
                  onClick={(e) => { e.stopPropagation(); handleCheckOne(f.id) }}
                  disabled={checkingId === f.id}
                  className="w-7 h-7 flex items-center justify-center text-xs rounded bg-white dark:bg-slate-700 text-slate-500 hover:text-emerald-500 cursor-pointer shadow-sm border border-slate-200 dark:border-slate-600"
                  aria-label={`Проверить фильтр ${f.name}`}
                >
                  {checkingId === f.id ? '⏳' : '▶'}
                </button>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); handleToggle(f.id) }}
                className="w-7 h-7 flex items-center justify-center text-xs rounded bg-white dark:bg-slate-700 text-slate-500 hover:text-blue-600 cursor-pointer shadow-sm border border-slate-200 dark:border-slate-600"
                aria-label={f.active ? 'Выключить' : 'Включить'}
              >
                {f.active ? '⏸' : '▶️'}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleClone(f.id) }}
                className="w-7 h-7 flex items-center justify-center text-xs rounded bg-white dark:bg-slate-700 text-slate-500 hover:text-blue-600 cursor-pointer shadow-sm border border-slate-200 dark:border-slate-600"
                aria-label="Клонировать"
              >
                📋
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setEditFilter(f) }}
                className="w-7 h-7 flex items-center justify-center text-xs rounded bg-white dark:bg-slate-700 text-slate-500 hover:text-blue-600 cursor-pointer shadow-sm border border-slate-200 dark:border-slate-600"
                aria-label="Редактировать"
              >
                ✏️
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setDeleteConfirm(f.id) }}
                className="w-7 h-7 flex items-center justify-center text-xs rounded bg-white dark:bg-slate-700 text-slate-500 hover:text-red-500 cursor-pointer shadow-sm border border-slate-200 dark:border-slate-600"
                aria-label="Удалить"
              >
                🗑
              </button>
            </div>
          </div>
        ))}
      </div>

      {editFilter && (
        <FilterModal config={config} filter={editFilter} onClose={() => setEditFilter(null)} onSaved={onRefresh} />
      )}

      <ConfirmModal
        open={deleteConfirm !== null}
        title="Удалить фильтр?"
        message="Это действие нельзя отменить."
        confirmLabel="Удалить"
        danger
        onConfirm={async () => {
          if (deleteConfirm !== null) {
            try {
              await api.deleteFilter(deleteConfirm)
              toast.success('Фильтр удалён')
              if (selectedId === deleteConfirm) onSelect(null)
              onRefresh()
            } catch { toast.error('Ошибка удаления') }
          }
          setDeleteConfirm(null)
        }}
        onCancel={() => setDeleteConfirm(null)}
      />
    </>
  )
}

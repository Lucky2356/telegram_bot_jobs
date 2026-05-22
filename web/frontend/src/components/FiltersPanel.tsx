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
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <p className="text-sm">Фильтров пока нет</p>
      </div>
    )
  }

  return (
    <>
      {filters.length > 5 && (
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск фильтров..."
          className="w-full mb-2 px-3 py-2 text-xs border border-slate-200/60 dark:border-slate-700/40 rounded-xl bg-white/70 dark:bg-slate-800/70 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary/40"
          aria-label="Поиск фильтров"
        />
      )}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => onSelect(null)}
          className={`px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
            selectedId === null
              ? 'bg-primary text-white border-primary shadow-sm'
              : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600 hover:border-primary'
          }`}
        >
          Все
        </button>
        {filtered.map((f) => (
          <div
            key={f.id}
            className={`group relative flex items-center gap-1 px-3 py-1.5 text-xs font-medium rounded-lg border transition-all cursor-pointer ${
              selectedId === f.id
                ? 'bg-primary text-white border-primary shadow-sm'
                : f.active
                  ? 'bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600 hover:border-primary'
                  : 'bg-gray-50 dark:bg-gray-800/50 text-gray-400 dark:text-gray-500 border-gray-200 dark:border-gray-700'
            }`}
            onClick={() => onSelect(f.id)}
            role="tab"
            aria-selected={selectedId === f.id}
            tabIndex={0}
            onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(f.id) }}}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${f.active ? 'bg-emerald-400' : 'bg-gray-300 dark:bg-gray-600'}`} />
            <span className={!f.active ? 'line-through' : ''}>{f.name}</span>

            {/* Quick actions */}
            <div className="hidden group-hover:flex items-center gap-0.5 ml-1">
              {f.active && (
                <button
                  onClick={(e) => { e.stopPropagation(); handleCheckOne(f.id) }}
                  disabled={checkingId === f.id}
                  className="w-5 h-5 flex items-center justify-center text-[10px] rounded bg-white dark:bg-gray-700 text-gray-500 hover:text-emerald-500 cursor-pointer shadow-sm border border-gray-200 dark:border-gray-600"
                  aria-label={`Проверить фильтр ${f.name}`}
                >
                  {checkingId === f.id ? '⏳' : '▶'}
                </button>
              )}
              <button
                onClick={(e) => { e.stopPropagation(); handleToggle(f.id) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded bg-white dark:bg-gray-700 text-gray-500 hover:text-primary cursor-pointer shadow-sm border border-gray-200 dark:border-gray-600"
                aria-label={f.active ? 'Выключить' : 'Включить'}
              >
                {f.active ? '⏸' : '▶️'}
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleClone(f.id) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded bg-white dark:bg-gray-700 text-gray-500 hover:text-primary cursor-pointer shadow-sm border border-gray-200 dark:border-gray-600"
                aria-label="Клонировать"
              >
                📋
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setEditFilter(f) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded bg-white dark:bg-gray-700 text-gray-500 hover:text-primary cursor-pointer shadow-sm border border-gray-200 dark:border-gray-600"
                aria-label="Редактировать"
              >
                ✏️
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); setDeleteConfirm(f.id) }}
                className="w-5 h-5 flex items-center justify-center text-[10px] rounded bg-white dark:bg-gray-700 text-gray-500 hover:text-red-500 cursor-pointer shadow-sm border border-gray-200 dark:border-gray-600"
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

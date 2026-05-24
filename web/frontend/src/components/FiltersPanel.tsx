import { useMemo, useState } from 'react'
import { Copy, Pencil, Play, Plus, Power, Trash2, Search } from 'lucide-react'
import type { VacancyFilter, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './toastBus'
import FilterModal from './FilterModal'
import ConfirmModal from './ConfirmModal'

interface FiltersPanelProps {
  filters: VacancyFilter[]
  config: AppConfig
  selectedId: number | null
  onSelect: (id: number | null) => void
  onRefresh: () => void
  onCreate: () => void
  onSavedFilter: (filter: VacancyFilter) => void
}

export default function FiltersPanel({
  filters,
  config,
  selectedId,
  onSelect,
  onRefresh,
  onCreate,
  onSavedFilter,
}: FiltersPanelProps) {
  const [editFilter, setEditFilter] = useState<VacancyFilter | null>(null)
  const [checkingId, setCheckingId] = useState<number | null>(null)
  const [search, setSearch] = useState('')
  const [deleteConfirm, setDeleteConfirm] = useState<number | null>(null)

  const filtered = useMemo(
    () => (search ? filters.filter((f) => f.name.toLowerCase().includes(search.toLowerCase())) : filters),
    [filters, search],
  )

  const handleToggle = async (id: number) => {
    try {
      const res = await api.toggleFilter(id)
      toast.success(res.active ? 'Фильтр включён' : 'Фильтр поставлен на паузу')
      onRefresh()
    } catch {
      toast.error('Не удалось обновить статус фильтра')
    }
  }

  const handleCheckOne = async (id: number) => {
    onSelect(id)
    setCheckingId(id)
    try {
      await api.checkFilter(id)
      toast.success('Проверка фильтра запущена')
      setTimeout(() => onRefresh(), 1500)
    } catch {
      toast.error('Ошибка запуска проверки')
    } finally {
      setCheckingId(null)
    }
  }

  const handleClone = async (id: number) => {
    try {
      await api.cloneFilter(id)
      toast.success('Фильтр успешно клонирован')
      onRefresh()
    } catch {
      toast.error('Не удалось клонировать фильтр')
    }
  }

  if (filters.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-[var(--border)] bg-[color:var(--surface-elevated)] p-6 text-center">
        <p className="text-sm font-medium text-primary">Фильтров ещё нет</p>
        <p className="mt-1 text-xs text-secondary">Создайте первый фильтр и запустите проверку вакансий.</p>
        <button
          type="button"
          onClick={onCreate}
          className="focus-ring mt-4 inline-flex h-10 max-w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
        >
          <Plus className="h-4 w-4 shrink-0" />
          <span className="btn-text">Создать фильтр</span>
        </button>
      </div>
    )
  }

  return (
    <>
      <div className="space-y-3">
        <button
          type="button"
          onClick={onCreate}
          className="focus-ring inline-flex h-10 w-full max-w-full items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
        >
          <Plus className="h-4 w-4 shrink-0" />
          <span className="btn-text">Новый фильтр</span>
        </button>

        {filters.length > 0 && (
          <div className="relative">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Поиск фильтра"
              className="focus-ring h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] pl-9 pr-3 text-sm text-primary placeholder:text-muted"
              aria-label="Поиск фильтров"
            />
          </div>
        )}

        <button
          onClick={() => onSelect(null)}
          className={`focus-ring inline-flex h-10 items-center rounded-2xl border px-3 text-sm font-medium transition ${
            selectedId === null
              ? 'border-[var(--border-strong)] bg-[var(--accent-soft)] text-primary'
              : 'border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary hover:text-primary'
          }`}
        >
          Все фильтры
        </button>

        <div className="space-y-2">
          {filtered.map((f) => (
            <div
              key={f.id}
              className={`rounded-2xl border p-3 transition ${
                selectedId === f.id
                  ? 'border-[var(--border-strong)] bg-[var(--accent-soft)]'
                  : 'border-[var(--border)] bg-[color:var(--surface-elevated)]'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <button
                  onClick={() => onSelect(f.id)}
                  className="focus-ring flex min-w-0 flex-1 items-center gap-2 rounded-lg text-left"
                >
                  <span className={`h-2 w-2 rounded-full ${f.active ? 'bg-emerald-400' : 'bg-slate-500'}`} />
                  <span className={`truncate text-sm font-medium ${f.active ? 'text-primary' : 'text-secondary line-through'}`}>
                    {f.name}
                  </span>
                </button>

                <div className="inline-flex items-center gap-1">
                  {f.active && (
                    <button
                      onClick={() => handleCheckOne(f.id)}
                      disabled={checkingId === f.id}
                      className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary transition hover:text-primary disabled:cursor-not-allowed disabled:opacity-50"
                      aria-label={`Проверить фильтр ${f.name}`}
                    >
                      <Play className="h-3.5 w-3.5" />
                    </button>
                  )}
                  <button
                    onClick={() => handleToggle(f.id)}
                    className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary transition hover:text-primary"
                    aria-label={f.active ? 'Выключить фильтр' : 'Включить фильтр'}
                  >
                    <Power className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => handleClone(f.id)}
                    className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary transition hover:text-primary"
                    aria-label="Клонировать фильтр"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setEditFilter(f)}
                    className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--border)] bg-[color:var(--surface-strong)] text-secondary transition hover:text-primary"
                    aria-label="Редактировать фильтр"
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => setDeleteConfirm(f.id)}
                    className="focus-ring inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-400/30 bg-rose-500/10 text-rose-300 transition hover:bg-rose-500/20"
                    aria-label="Удалить фильтр"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {editFilter && (
        <FilterModal
          key={`edit-${editFilter.id}`}
          config={config}
          filter={editFilter}
          onClose={() => setEditFilter(null)}
          onSaved={(saved) => {
            setEditFilter(null)
            onSavedFilter(saved)
          }}
        />
      )}

      <ConfirmModal
        open={deleteConfirm !== null}
        title="Удалить фильтр?"
        message="Это действие нельзя отменить. История отправок по вакансиям останется в системе."
        confirmLabel="Удалить"
        danger
        onConfirm={async () => {
          if (deleteConfirm !== null) {
            try {
              await api.deleteFilter(deleteConfirm)
              toast.success('Фильтр удалён')
              if (selectedId === deleteConfirm) onSelect(null)
              onRefresh()
            } catch {
              toast.error('Ошибка удаления фильтра')
            }
          }
          setDeleteConfirm(null)
        }}
        onCancel={() => setDeleteConfirm(null)}
      />
    </>
  )
}

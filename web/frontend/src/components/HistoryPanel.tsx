import { useState, useMemo, useCallback } from 'react'
import type { HistoryItem, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './Toast'

interface HistoryPanelProps {
  config: AppConfig
}

const sourceColors: Record<string, string> = {
  hh: 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300',
  superjob: 'bg-cyan-50 text-cyan-700 dark:bg-cyan-900/20 dark:text-cyan-300',
  trudvsem: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-900/20 dark:text-emerald-300',
  rabota: 'bg-amber-50 text-amber-700 dark:bg-amber-900/20 dark:text-amber-300',
  habr: 'bg-rose-50 text-rose-700 dark:bg-rose-900/20 dark:text-rose-300',
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России',
  rabota: 'rabota.ru', habr: 'Хабр Карьера',
}

function groupByDate(items: HistoryItem[]): [string, HistoryItem[]][] {
  const groups: Record<string, HistoryItem[]> = {}
  const now = new Date()
  const today = now.toDateString()
  const yesterday = new Date(now.getTime() - 86400000).toDateString()

  for (const h of items) {
    const date = new Date(h.sent_at)
    const dateStr = date.toDateString()
    let label: string
    if (dateStr === today) label = 'Сегодня'
    else if (dateStr === yesterday) label = 'Вчера'
    else if ((now.getTime() - date.getTime()) / 86400000 < 7) label = 'На этой неделе'
    else label = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
    ;(groups[label] ??= []).push(h)
  }
  return Object.entries(groups)
}

export default function HistoryPanel({ config }: HistoryPanelProps) {
  const [items, setItems] = useState<HistoryItem[]>([])
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(true)
  const [loading, setLoading] = useState(false)
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')

  const fetchPage = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const data = await api.getHistory(p, 20)
      if (p === 1) {
        setItems(data.items)
      } else {
        setItems((prev) => [...prev, ...data.items])
      }
      setHasMore(data.has_more)
      setPage(p)
    } catch {
      toast.error('Ошибка загрузки истории')
    } finally {
      setLoading(false)
    }
  }, [])

  const sources = useMemo(() => {
    const set = new Set(items.map((h) => h.source))
    return Array.from(set).sort()
  }, [items])

  const filtered = useMemo(() => {
    return items.filter((h) => {
      if (sourceFilter && h.source !== sourceFilter) return false
      if (search) {
        const q = search.toLowerCase()
        return (
          h.vacancy_title.toLowerCase().includes(q) ||
          (h.company?.toLowerCase().includes(q) ?? false) ||
          (h.filter_name?.toLowerCase().includes(q) ?? false)
        )
      }
      return true
    })
  }, [items, search, sourceFilter])

  const groups = useMemo(() => groupByDate(filtered), [filtered])

  if (items.length === 0 && !loading) {
    fetchPage(1)
  }

  if (items.length === 0 && loading) {
    return (
      <div className="text-center py-12 text-gray-400">
        <p>⏳ Загрузка истории...</p>
      </div>
    )
  }

  return (
    <div>
      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск по названию, компании или фильтру..."
          className="flex-1 min-w-[200px] px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Поиск в истории"
        />
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Фильтр по сайту"
        >
          <option value="">Все сайты</option>
          {sources.map((s) => (
            <option key={s} value={s}>{config.sites[s] || sourceLabels[s] || s}</option>
          ))}
        </select>
        <button
          onClick={() => fetchPage(1)}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
          aria-label="Обновить историю"
        >
          🔄
        </button>
      </div>

      {filtered.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-base">Ничего не найдено</p>
        </div>
      )}

      {/* Grouped cards */}
      <div className="space-y-6">
        {groups.map(([label, groupItems]) => (
          <div key={label}>
            <h3 className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider mb-3">
              {label}
              <span className="ml-2 font-normal text-gray-300 dark:text-gray-600">{groupItems.length}</span>
            </h3>
            <div className="space-y-2">
              {groupItems.map((h, idx) => (
                <a
                  key={`${h.sent_at}-${idx}`}
                  href={h.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-3.5 hover:shadow-md hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200 group"
                  aria-label={`Открыть ${h.vacancy_title}`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary transition-colors">
                        {h.vacancy_title}
                      </p>
                      <div className="flex items-center gap-2 mt-1 text-xs text-gray-500 dark:text-gray-400 flex-wrap">
                        {h.company && <span>🏢 {h.company}</span>}
                        {h.salary && <span className="text-emerald-600 dark:text-emerald-400 font-medium">💰 {h.salary}</span>}
                        {h.filter_name && <span className="text-gray-400">📋 {h.filter_name}</span>}
                      </div>
                    </div>
                    <div className="flex flex-col items-end gap-1 shrink-0">
                      <span
                        className={`px-2 py-0.5 text-[10px] font-medium rounded-md ${
                          sourceColors[h.source] || 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                        }`}
                      >
                        {sourceLabels[h.source] || h.source}
                      </span>
                      <span className="text-[10px] text-gray-400 dark:text-gray-500 whitespace-nowrap">
                        {new Date(h.sent_at).toLocaleString('ru-RU', {
                          hour: '2-digit', minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                </a>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Load more */}
      {hasMore && (
        <div className="text-center mt-6">
          <button
            onClick={() => fetchPage(page + 1)}
            disabled={loading}
            className="px-6 py-2.5 text-sm font-medium text-primary border border-primary/30 rounded-xl hover:bg-primary hover:text-white transition-all disabled:opacity-50 cursor-pointer"
            aria-label="Загрузить ещё"
          >
            {loading ? '⏳ Загрузка...' : '📥 Загрузить ещё'}
          </button>
        </div>
      )}
    </div>
  )
}

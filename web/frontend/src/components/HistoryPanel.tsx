import { useState, useMemo, useCallback, useEffect, useRef } from 'react'
import { Search, RefreshCw } from 'lucide-react'
import type { HistoryItem, AppConfig } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface HistoryPanelProps {
  config: AppConfig
}

const sourceLabels: Record<string, string> = {
  hh: 'hh.ru',
  superjob: 'SuperJob',
  trudvsem: 'Работа России',
  rabota: 'rabota.ru',
  habr: 'Хабр Карьера',
}

function groupByDate(items: HistoryItem[]): [string, HistoryItem[]][] {
  const groups: Record<string, HistoryItem[]> = {}
  const now = new Date()
  const today = now.toDateString()
  const yesterday = new Date(now.getTime() - 86400000).toDateString()

  for (const h of items) {
    const date = new Date(h.sent_at)
    const dateStr = date.toDateString()
    let label = date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'long' })
    if (dateStr === today) label = 'Сегодня'
    else if (dateStr === yesterday) label = 'Вчера'
    else if ((now.getTime() - date.getTime()) / 86400000 < 7) label = 'Эта неделя'

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
  const sentinelRef = useRef<HTMLDivElement | null>(null)

  const fetchPage = useCallback(async (p: number) => {
    setLoading(true)
    try {
      const data = await api.getHistory(p, 20)
      setItems((prev) => (p === 1 ? data.items : [...prev, ...data.items]))
      setHasMore(data.has_more)
      setPage(p)
    } catch {
      toast.error('Не удалось загрузить историю')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    if (items.length === 0 && !loading) {
      const timer = setTimeout(() => {
        void fetchPage(1)
      }, 0)
      return () => clearTimeout(timer)
    }
  }, [items.length, loading, fetchPage])

  useEffect(() => {
    if (!hasMore || loading) return
    const sentinel = sentinelRef.current
    if (!sentinel) return

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          void fetchPage(page + 1)
        }
      },
      { rootMargin: '180px' },
    )

    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [hasMore, loading, page, fetchPage])

  const sources = useMemo(() => Array.from(new Set(items.map((h) => h.source))).sort(), [items])

  const filtered = useMemo(
    () => items.filter((h) => {
      if (sourceFilter && h.source !== sourceFilter) return false
      if (!search) return true
      const q = search.toLowerCase()
      return (
        h.vacancy_title.toLowerCase().includes(q)
        || (h.company?.toLowerCase().includes(q) ?? false)
        || (h.filter_name?.toLowerCase().includes(q) ?? false)
      )
    }),
    [items, sourceFilter, search],
  )

  const groups = useMemo(() => groupByDate(filtered), [filtered])

  if (items.length === 0 && loading) {
    return <p className="text-sm text-secondary">Загружаем историю...</p>
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-2 md:grid-cols-12">
        <div className="relative md:col-span-7">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по вакансии, компании или названию фильтра"
            className="focus-ring h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] pl-9 pr-3 text-sm text-primary placeholder:text-muted"
          />
        </div>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="focus-ring h-10 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary md:col-span-3"
          aria-label="Фильтр по источнику"
        >
          <option value="">Все источники</option>
          {sources.map((s) => (
            <option key={s} value={s}>{config.sites[s] || sourceLabels[s] || s}</option>
          ))}
        </select>

        <button
          onClick={() => fetchPage(1)}
          className="focus-ring inline-flex h-10 items-center justify-center rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary transition hover:text-primary md:col-span-2"
          aria-label="Обновить историю"
        >
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      {filtered.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border)] bg-[color:var(--surface-elevated)] p-8 text-center">
          <p className="text-base font-medium text-primary">История пока пустая</p>
          <p className="mt-2 text-sm text-secondary">Запустите проверку и дождитесь отправки вакансий в Telegram.</p>
        </div>
      )}

      <div className="space-y-5">
        {groups.map(([dateLabel, dateItems]) => (
          <section key={dateLabel} className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              {dateLabel}
              <span className="ml-2 rounded-full border border-[var(--border)] px-2 py-0.5 text-[10px] font-medium text-secondary">
                {dateItems.length}
              </span>
            </h3>

            {dateItems.map((item, idx) => (
              <a
                key={`${item.sent_at}-${idx}`}
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3 transition hover:border-[var(--border-strong)]"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-primary">{item.vacancy_title}</p>
                    <div className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-secondary">
                      {item.company && <span>{item.company}</span>}
                      {item.salary && <span className="font-semibold text-emerald-400">{item.salary}</span>}
                      {item.filter_name && (
                        <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-[10px]">{item.filter_name}</span>
                      )}
                    </div>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                      {sourceLabels[item.source] || item.source}
                    </p>
                    <p className="mt-1 text-[10px] text-secondary">
                      {new Date(item.sent_at).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              </a>
            ))}
          </section>
        ))}
      </div>

      {hasMore && (
        <div ref={sentinelRef} className="py-2 text-center text-xs text-secondary">
          {loading ? 'Загружаем ещё...' : 'Прокрутите ниже для загрузки'}
        </div>
      )}
    </div>
  )
}

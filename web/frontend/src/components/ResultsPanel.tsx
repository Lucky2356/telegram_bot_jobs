import { useMemo, useState, useEffect, useRef } from 'react'
import type { VacancyResult, VacancyFilter, AppConfig } from '../types'
import VacancyCard from './VacancyCard'

interface ResultsPanelProps {
  results: VacancyResult[]
  config: AppConfig
  checkedAt: string | null
  checking: boolean
  filters: VacancyFilter[]
  selectedFilterId: number | null
  onRefreshResults: () => void
}

type SortKey = 'date-desc' | 'date-asc' | 'salary-desc' | 'salary-asc'

export default function ResultsPanel({
  results, config, checkedAt, checking, filters, selectedFilterId, onRefreshResults,
}: ResultsPanelProps) {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('date-desc')
  const [groupBy, setGroupBy] = useState(false)
  const prevCountRef = useRef(0)

  useEffect(() => {
    if (checking) {
      const timer = setInterval(onRefreshResults, 3000)
      return () => clearInterval(timer)
    }
  }, [checking, onRefreshResults])

  if (!checking) prevCountRef.current = results.length

  const sources = useMemo(() => {
    const set = new Set(results.map((v) => v.source))
    return Array.from(set).sort()
  }, [results])

  const processed = useMemo(() => {
    let items = [...results]

    if (search) {
      const q = search.toLowerCase()
      items = items.filter((v) =>
        v.title.toLowerCase().includes(q) ||
        (v.company?.toLowerCase().includes(q) ?? false)
      )
    }

    if (sourceFilter) {
      items = items.filter((v) => v.source === sourceFilter)
    }

    items.sort((a, b) => {
      if (sortKey === 'date-desc' || sortKey === 'date-asc') {
        const da = a.published_at ? new Date(a.published_at).getTime() : 0
        const db = b.published_at ? new Date(b.published_at).getTime() : 0
        return sortKey === 'date-desc' ? db - da : da - db
      }
      const extractSalary = (v: VacancyResult) => {
        const nums = v.salary_text?.match(/\d[\d\s]*/g)
        if (!nums) return 0
        const vals = nums.map((n) => parseInt(n.replace(/\s/g, '')))
        return vals.reduce((a, b) => Math.max(a, b), 0)
      }
      return sortKey === 'salary-desc'
        ? extractSalary(b) - extractSalary(a)
        : extractSalary(a) - extractSalary(b)
    })

    return items
  }, [results, search, sourceFilter, sortKey])

  const groups = useMemo(() => {
    if (!groupBy) return null
    const map: Record<string, VacancyResult[]> = {}
    for (const v of processed) {
      const key = config.sites[v.source] || v.source
      ;(map[key] ??= []).push(v)
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
  }, [processed, groupBy, config.sites])

  const selectedFilter = filters.find((f) => f.id === selectedFilterId)

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2 mb-3">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            {selectedFilter ? (
              <><span className="text-primary">{selectedFilter.name}</span> — {processed.length}</>
            ) : (
              <>{processed.length} {processed.length === 1 ? 'вакансия' : processed.length < 5 ? 'вакансии' : 'вакансий'}</>
            )}
          </h2>
          {checking && (
            <span className="flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-full border border-amber-200 dark:border-amber-800">
              <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-ping" />
              Поиск...
            </span>
          )}
        </div>
        {checkedAt && !checking && (
          <span className="text-[10px] text-gray-400">
            {new Date(checkedAt).toLocaleString('ru-RU', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </span>
        )}
      </div>

      {/* Search + Filter + Sort */}
      <div className="flex flex-wrap gap-2 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск среди результатов..."
          className="flex-1 min-w-[160px] px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Поиск в результатах"
        />
        {sources.length > 1 && (
          <select
            value={sourceFilter}
            onChange={(e) => setSourceFilter(e.target.value)}
            className="px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="Фильтр по сайту"
          >
            <option value="">Все сайты</option>
            {sources.map((s) => (
              <option key={s} value={s}>{config.sites[s] || s}</option>
            ))}
          </select>
        )}
        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Сортировка"
        >
          <option value="date-desc">📅 Сначала новые</option>
          <option value="date-asc">📅 Сначала старые</option>
          <option value="salary-desc">💰 По убыванию</option>
          <option value="salary-asc">💰 По возрастанию</option>
        </select>
        <button
          onClick={() => setGroupBy(!groupBy)}
          className={`px-3 py-2 text-xs rounded-lg border transition-all cursor-pointer ${
            groupBy
              ? 'bg-primary text-white border-primary'
              : 'border-gray-200 dark:border-gray-700 text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
          aria-label="Группировать по сайту"
        >
          📂 Группы
        </button>
        <button
          onClick={onRefreshResults}
          className="px-3 py-2 text-xs border border-gray-200 dark:border-gray-700 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
          aria-label="Обновить"
        >
          🔄
        </button>
      </div>

      {/* Empty state */}
      {results.length === 0 && !checking && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm mb-1">🔍 Ничего не найдено</p>
          <p className="text-xs">Нажми «Проверить» или измени фильтры</p>
        </div>
      )}

      {results.length === 0 && checking && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm mb-1">⏳ Поиск вакансий...</p>
          <p className="text-xs">Вакансии скоро появятся</p>
        </div>
      )}

      {results.length > 0 && processed.length === 0 && !checking && (
        <div className="text-center py-8 text-gray-400">
          <p className="text-xs">Ничего не найдено по вашему запросу</p>
        </div>
      )}

      {/* Results */}
      {processed.length > 0 && (
        <>
          {groups ? (
            <div className="space-y-4">
              {groups.map(([site, siteItems]) => (
                <div key={site}>
                  <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                    <span>{site}</span>
                    <span className="text-gray-300 dark:text-gray-600 font-normal">{siteItems.length}</span>
                  </h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
                    {siteItems.map((v, idx) => (
                      <div key={`${v.source}-${v.url}-${idx}`} className="animate-fade-in" style={{ animationDelay: `${idx * 20}ms` }}>
                        <VacancyCard vacancy={v} config={config} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
              {processed.map((v, idx) => (
                <div key={`${v.source}-${v.url}-${idx}`} className="animate-fade-in" style={{ animationDelay: `${idx * 20}ms` }}>
                  <VacancyCard vacancy={v} config={config} />
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

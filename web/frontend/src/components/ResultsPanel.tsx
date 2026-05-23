import { useMemo, useState } from 'react'
import { Search, RefreshCw, Layers3 } from 'lucide-react'
import type { VacancyResult, VacancyFilter, AppConfig } from '../types'
import VacancyCard from './VacancyCard'
import VacancyDetail from './VacancyDetail'

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

function salaryRank(v: VacancyResult) {
  const nums = v.salary_text?.match(/\d[\d\s]*/g)
  if (!nums) return 0
  const values = nums.map((n) => parseInt(n.replace(/\s/g, ''), 10)).filter((n) => !Number.isNaN(n))
  return values.reduce((acc, item) => Math.max(acc, item), 0)
}

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {Array.from({ length: 6 }).map((_, idx) => (
        <div key={idx} className="bento-card p-4">
          <div className="skeleton h-4 w-2/3 rounded" />
          <div className="skeleton mt-2 h-3 w-1/2 rounded" />
          <div className="skeleton mt-3 h-4 w-1/3 rounded" />
          <div className="skeleton mt-4 h-16 w-full rounded-xl" />
          <div className="mt-4 grid grid-cols-3 gap-2">
            <div className="skeleton h-8 rounded-lg" />
            <div className="skeleton h-8 rounded-lg" />
            <div className="skeleton h-8 rounded-lg" />
          </div>
        </div>
      ))}
    </div>
  )
}

export default function ResultsPanel({
  results,
  config,
  checkedAt,
  checking,
  filters,
  selectedFilterId,
  onRefreshResults,
}: ResultsPanelProps) {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [sortKey, setSortKey] = useState<SortKey>('date-desc')
  const [groupBy, setGroupBy] = useState(false)
  const [detailVacancy, setDetailVacancy] = useState<VacancyResult | null>(null)

  const selectedFilter = filters.find((f) => f.id === selectedFilterId)

  const sources = useMemo(() => {
    const sourceSet = new Set(results.map((v) => v.source))
    return Array.from(sourceSet).sort()
  }, [results])

  const processed = useMemo(() => {
    let items = [...results]

    if (search) {
      const q = search.toLowerCase()
      items = items.filter((v) =>
        v.title.toLowerCase().includes(q)
        || (v.company?.toLowerCase().includes(q) ?? false)
        || (v.description?.toLowerCase().includes(q) ?? false),
      )
    }

    if (sourceFilter) items = items.filter((v) => v.source === sourceFilter)

    if (sortKey === 'date-desc' || sortKey === 'date-asc') {
      items = [...items].sort((a, b) => {
        const da = a.published_at ? new Date(a.published_at).getTime() : 0
        const db = b.published_at ? new Date(b.published_at).getTime() : 0
        return sortKey === 'date-desc' ? db - da : da - db
      })
    } else {
      items = [...items].sort((a, b) =>
        sortKey === 'salary-desc' ? salaryRank(b) - salaryRank(a) : salaryRank(a) - salaryRank(b),
      )
    }

    return items
  }, [results, search, sourceFilter, sortKey])

  const grouped = useMemo(() => {
    if (!groupBy) return null
    const map: Record<string, VacancyResult[]> = {}
    for (const item of processed) {
      const key = config.sites[item.source] || item.source
      ;(map[key] ??= []).push(item)
    }
    return Object.entries(map).sort(([a], [b]) => a.localeCompare(b))
  }, [groupBy, processed, config.sites])

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-primary">
            {selectedFilter ? selectedFilter.name : 'Все результаты'}
          </h2>
          <p className="mt-1 text-xs text-secondary">
            Найдено: <span className="code text-primary">{processed.length}</span>
            {checkedAt && !checking && ` · обновлено ${new Date(checkedAt).toLocaleString('ru-RU', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}`}
          </p>
        </div>

        {checking && (
          <span className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--accent-soft)] px-3 py-1 text-xs font-semibold text-primary">
            <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--accent)]" />
            Идёт проверка
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-2 md:grid-cols-12">
        <div className="relative md:col-span-6">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск по названию, компании или описанию"
            className="focus-ring h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] pl-9 pr-3 text-sm text-primary placeholder:text-muted"
            aria-label="Поиск по результатам"
          />
        </div>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="focus-ring h-10 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary md:col-span-2"
          aria-label="Фильтр по источнику"
        >
          <option value="">Все источники</option>
          {sources.map((s) => (
            <option key={s} value={s}>{config.sites[s] || s}</option>
          ))}
        </select>

        <select
          value={sortKey}
          onChange={(e) => setSortKey(e.target.value as SortKey)}
          className="focus-ring h-10 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary md:col-span-2"
          aria-label="Сортировка результатов"
        >
          <option value="date-desc">Сначала новые</option>
          <option value="date-asc">Сначала старые</option>
          <option value="salary-desc">Высокая зарплата</option>
          <option value="salary-asc">Низкая зарплата</option>
        </select>

        <div className="flex items-center gap-2 md:col-span-2 md:justify-end">
          <button
            onClick={() => setGroupBy((prev) => !prev)}
            className={`focus-ring inline-flex h-10 items-center justify-center gap-1 rounded-xl border px-3 text-sm font-medium transition ${
              groupBy
                ? 'border-[var(--border-strong)] bg-[var(--accent-soft)] text-primary'
                : 'border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary hover:text-primary'
            }`}
            aria-label="Группировать результаты"
          >
            <Layers3 className="h-4 w-4" />
            Группы
          </button>
          <button
            onClick={onRefreshResults}
            className="focus-ring inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] text-secondary transition hover:text-primary"
            aria-label="Обновить результаты"
          >
            <RefreshCw className="h-4 w-4" />
          </button>
        </div>
      </div>

      {results.length === 0 && checking && <SkeletonGrid />}

      {results.length === 0 && !checking && (
        <div className="bento-card p-8 text-center">
          <p className="text-base font-medium text-primary">Пока нет найденных вакансий</p>
          <p className="mt-2 text-sm text-secondary">Запустите проверку или расширьте фильтры, чтобы увидеть первую подборку.</p>
        </div>
      )}

      {results.length > 0 && processed.length === 0 && !checking && (
        <div className="bento-card p-8 text-center">
          <p className="text-base font-medium text-primary">Ничего не найдено по текущему запросу</p>
          <p className="mt-2 text-sm text-secondary">Сбросьте часть фильтров или измените текст поиска.</p>
        </div>
      )}

      {processed.length > 0 && (
        grouped ? (
          <div className="space-y-5">
            {grouped.map(([sourceName, items]) => (
              <section key={sourceName} className="space-y-3">
                <h3 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted">
                  <span>{sourceName}</span>
                  <span className="rounded-full border border-[var(--border)] px-2 py-0.5 text-[10px] text-secondary">{items.length}</span>
                </h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {items.map((vacancy, idx) => (
                    <div key={`${vacancy.source}-${vacancy.url}`} className="animate-fade-in-up" style={{ animationDelay: `${idx * 22}ms` }}>
                      <VacancyCard vacancy={vacancy} config={config} onDetail={setDetailVacancy} />
                    </div>
                  ))}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {processed.map((vacancy, idx) => (
              <div key={`${vacancy.source}-${vacancy.url}`} className="animate-fade-in-up" style={{ animationDelay: `${idx * 18}ms` }}>
                <VacancyCard vacancy={vacancy} config={config} onDetail={setDetailVacancy} />
              </div>
            ))}
          </div>
        )
      )}

      {detailVacancy && (
        <VacancyDetail vacancy={detailVacancy} config={config} onClose={() => setDetailVacancy(null)} />
      )}
    </div>
  )
}

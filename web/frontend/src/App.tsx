import { useState, useEffect, useCallback, lazy, Suspense } from 'react'
import type { VacancyFilter, Stats, AppConfig, VacancyResult, SavedVacancy, BlocklistItem, ParserStatus } from './types'
import { api } from './api'
import Tabs from './components/Tabs'
import FiltersPanel from './components/FiltersPanel'
import ResultsPanel from './components/ResultsPanel'
import HistoryPanel from './components/HistoryPanel'
const StatsPanel = lazy(() => import('./components/StatsPanel'))
import SavedPanel from './components/SavedPanel'
import BlocklistPanel from './components/BlocklistPanel'
import StatusBar from './components/StatusBar'
import FilterModal from './components/FilterModal'
import ErrorBoundary from './components/ErrorBoundary'
import Toast, { toast } from './components/Toast'

const TABS = [
  { key: 'search', label: '🔍 Поиск' },
  { key: 'history', label: '📨 История' },
  { key: 'saved', label: '📁 Избранное' },
  { key: 'stats', label: '📊 Статистика' },
]

const loadingSpinner = (
  <div className="text-center py-20 text-slate-400">
    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
    <p className="mt-3 text-sm">Загрузка...</p>
  </div>
)

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [status, setStatus] = useState<ParserStatus | null>(null)
  const [filters, setFilters] = useState<VacancyFilter[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [results, setResults] = useState<VacancyResult[]>([])
  const [checkedAt, setCheckedAt] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [saved, setSaved] = useState<SavedVacancy[]>([])
  const [blocklist, setBlocklist] = useState<BlocklistItem[]>([])
  const [activeTab, setActiveTab] = useState('search')
  const [selectedFilterId, setSelectedFilterId] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [dark, setDark] = useState(() => {
    try {
      const saved = localStorage.getItem('theme')
      if (saved) return saved === 'dark'
    } catch { /* ignore */ }
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('theme', dark ? 'dark' : 'light') } catch { /* ignore */ }
  }, [dark])

  const toggleTheme = () => setDark((prev) => !prev)

  const fetchConfig = useCallback(async () => {
    try { setConfig(await api.getConfig()) } catch { /* ignore */ }
  }, [])

  const fetchStatus = useCallback(async () => {
    try { setStatus(await api.getStatus()) } catch { /* ignore */ }
  }, [])

  const fetchFilters = useCallback(async () => {
    try { setFilters(await api.getFilters()) } catch { toast.error('Ошибка загрузки фильтров') }
  }, [])

  const fetchStats = useCallback(async () => {
    try { setStats(await api.getStats()) } catch { toast.error('Ошибка загрузки статистики') }
  }, [])

  const fetchResults = useCallback(async () => {
    try {
      const data = await api.getResults()
      setResults(data.items)
      setCheckedAt(data.checked_at)
      setChecking(data.checking)
    } catch { /* ignore */ }
  }, [])

  const fetchSaved = useCallback(async () => {
    try { setSaved(await api.getSaved()) } catch { /* ignore */ }
  }, [])

  const fetchBlocklist = useCallback(async () => {
    try { setBlocklist(await api.getBlocklist()) } catch { /* ignore */ }
  }, [])

  useEffect(() => { fetchConfig(); fetchStatus() }, [fetchConfig, fetchStatus])

  useEffect(() => {
    if (activeTab === 'search') { fetchFilters(); fetchResults() }
    else if (activeTab === 'saved') { fetchSaved(); fetchBlocklist() }
    else if (activeTab === 'stats') fetchStats()
  }, [activeTab, fetchFilters, fetchResults, fetchSaved, fetchBlocklist, fetchStats])

  const [checkingNow, setCheckingNow] = useState(false)

  const handleCheckNow = async () => {
    setCheckingNow(true)
    try {
      await api.checkNow()
      toast.success('Проверка запущена!')
      setChecking(true)
      setTimeout(() => fetchResults(), 2000)
    } catch { toast.error('Ошибка') }
    finally { setCheckingNow(false) }
  }

  const handleRefresh = useCallback(() => {
    fetchFilters(); fetchResults(); fetchStats(); fetchSaved(); fetchBlocklist()
  }, [fetchFilters, fetchResults, fetchStats, fetchSaved, fetchBlocklist])

  const handleCloseFilter = useCallback(() => setCreateOpen(false), [])
  const handleSavedFilter = useCallback(() => { handleRefresh(); fetchResults() }, [handleRefresh, fetchResults])

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Sticky glass header */}
      <div className="sticky top-0 z-30 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md border-b border-slate-200/60 dark:border-slate-700/40">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-3">
              <h1 className="text-lg font-bold text-slate-900 dark:text-slate-100 tracking-tight">
                🔍 Job Bot
              </h1>
              <StatusBar status={status} />
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => { setCreateOpen(true); setSelectedFilterId(null) }}
                className="px-3.5 py-2 text-xs font-medium bg-primary/10 text-primary rounded-xl hover:bg-primary hover:text-white transition-all cursor-pointer"
              >
                ➕ Фильтр
              </button>
              <button
                onClick={toggleTheme}
                className="px-3 py-2 text-xs border border-slate-200/60 dark:border-slate-700/40 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-slate-500 dark:text-slate-400"
                aria-label={dark ? 'Светлая тема' : 'Тёмная тема'}
              >
                {dark ? '☀️' : '🌙'}
              </button>
            </div>
          </div>

          {/* Tabs */}
          <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 py-5">
        {activeTab === 'search' && config && (
          <ErrorBoundary>
            <div className="space-y-4">
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 p-4">
                <FiltersPanel filters={filters} config={config} selectedId={selectedFilterId} onSelect={setSelectedFilterId} onRefresh={handleRefresh} />
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={handleCheckNow}
                  disabled={checkingNow}
                  className="px-5 py-2.5 text-sm font-medium bg-primary text-white rounded-xl hover:bg-primary-hover disabled:opacity-50 transition-all cursor-pointer shadow-sm"
                >
                  {checkingNow || checking ? '⏳ Проверка...' : '🔍 Проверить сейчас'}
                </button>
                <button
                  onClick={fetchResults}
                  className="px-4 py-2.5 text-sm border border-slate-200/60 dark:border-slate-700/40 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-slate-600 dark:text-slate-400"
                >
                  🔄 Обновить
                </button>
              </div>

              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 p-4">
                <ResultsPanel
                  results={results} config={config} checkedAt={checkedAt} checking={checking}
                  filters={filters} selectedFilterId={selectedFilterId} onRefreshResults={fetchResults}
                />
              </div>
            </div>
          </ErrorBoundary>
        )}

        {activeTab === 'history' && config && (
          <ErrorBoundary>
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 p-4">
              <HistoryPanel config={config} />
            </div>
          </ErrorBoundary>
        )}

        {activeTab === 'saved' && config && (
          <ErrorBoundary>
            <div className="space-y-4">
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 p-4">
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">📌 Сохранённые вакансии</h2>
                <SavedPanel saved={saved} config={config} onRefresh={fetchSaved} />
              </div>
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl shadow-sm border border-slate-200/60 dark:border-slate-700/40 p-4">
                <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">🚫 Блок-лист</h2>
                <BlocklistPanel items={blocklist} onRefresh={fetchBlocklist} />
              </div>
            </div>
          </ErrorBoundary>
        )}

        {activeTab === 'stats' && stats && (
          <ErrorBoundary>
            <Suspense fallback={<div className="text-center py-20 text-slate-400"><p className="text-sm">Загрузка графиков...</p></div>}>
              <StatsPanel stats={stats} />
            </Suspense>
          </ErrorBoundary>
        )}

        {!config && loadingSpinner}
      </div>

      {createOpen && config && (
        <FilterModal
          config={config}
          filter={null}
          onClose={handleCloseFilter}
          onSaved={handleSavedFilter}
        />
      )}

      <Toast />
    </div>
  )
}

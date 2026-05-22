import { useState, useEffect, useCallback } from 'react'
import type { VacancyFilter, Stats, AppConfig, VacancyResult } from './types'
import { api } from './api'
import Tabs from './components/Tabs'
import FiltersPanel from './components/FiltersPanel'
import ResultsPanel from './components/ResultsPanel'
import HistoryPanel from './components/HistoryPanel'
import StatsPanel from './components/StatsPanel'
import FilterModal from './components/FilterModal'
import Toast, { toast } from './components/Toast'

const TABS = [
  { key: 'search', label: '🔍 Поиск' },
  { key: 'history', label: '📨 История' },
  { key: 'stats', label: '📊 Статистика' },
]

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [filters, setFilters] = useState<VacancyFilter[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [results, setResults] = useState<VacancyResult[]>([])
  const [checkedAt, setCheckedAt] = useState<string | null>(null)
  const [checking, setChecking] = useState(false)
  const [activeTab, setActiveTab] = useState('search')
  const [selectedFilterId, setSelectedFilterId] = useState<number | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const toggleTheme = () => setDark((prev) => !prev)

  const fetchConfig = useCallback(async () => {
    try { setConfig(await api.getConfig()) } catch { console.error('config fail') }
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
    } catch { toast.error('Ошибка загрузки результатов') }
  }, [])

  useEffect(() => { fetchConfig() }, [fetchConfig])

  useEffect(() => {
    if (activeTab === 'search') { fetchFilters(); fetchResults() }
    else if (activeTab === 'stats') fetchStats()
  }, [activeTab, fetchFilters, fetchResults, fetchStats])

  const [checkingNow, setCheckingNow] = useState(false)

  const handleCheckNow = async () => {
    setCheckingNow(true)
    try {
      await api.checkNow()
      toast.success('Проверка запущена!')
      setChecking(true)
      setTimeout(() => fetchResults(), 2000)
    } catch { toast.error('Ошибка запуска проверки') }
    finally { setCheckingNow(false) }
  }

  const handleRefresh = useCallback(() => {
    fetchFilters()
    fetchResults()
    fetchStats()
  }, [fetchFilters, fetchResults, fetchStats])

  const filteredResults = selectedFilterId
    ? results
    : results

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-6xl mx-auto px-4 py-5">
        {/* Header bar */}
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">
              🔍 Job Bot
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setCreateOpen(true); setSelectedFilterId(null) }}
              className="px-3 py-1.5 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
              aria-label="Создать фильтр"
            >
              ➕ Фильтр
            </button>
            <button
              onClick={toggleTheme}
              className="px-3 py-1.5 text-xs border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
              aria-label={dark ? 'Светлая тема' : 'Тёмная тема'}
            >
              {dark ? '☀️' : '🌙'}
            </button>
          </div>
        </div>

        {/* Tabs */}
        <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />

        {/* Filters + Results (merged) */}
        {activeTab === 'search' && config && (
          <div className="space-y-4">
            {/* Filter selector bar */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-3.5">
              <FiltersPanel
                filters={filters}
                config={config}
                selectedId={selectedFilterId}
                onSelect={setSelectedFilterId}
                onRefresh={handleRefresh}
              />
            </div>

            {/* Check button inline */}
            <div className="flex items-center gap-2">
              <button
                onClick={handleCheckNow}
                disabled={checkingNow}
                className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-xl hover:bg-primary-hover disabled:opacity-50 transition-all cursor-pointer shadow-sm"
                aria-label="Проверить вакансии"
              >
                {checkingNow || checking ? '⏳ Проверка...' : '🔍 Проверить сейчас'}
              </button>
              <button
                onClick={fetchResults}
                className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
                aria-label="Обновить результаты"
              >
                🔄 Обновить
              </button>
            </div>

            {/* Results */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <ResultsPanel
                results={filteredResults}
                config={config}
                checkedAt={checkedAt}
                checking={checking}
                filters={filters}
                selectedFilterId={selectedFilterId}
                onRefreshResults={fetchResults}
              />
            </div>
          </div>
        )}

        {/* History tab */}
        {activeTab === 'history' && config && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <HistoryPanel config={config} />
          </div>
        )}

        {/* Stats tab */}
        {activeTab === 'stats' && stats && (
          <StatsPanel stats={stats} />
        )}

        {!config && (
          <div className="text-center py-20 text-gray-400">
            <p>Загрузка...</p>
          </div>
        )}
      </div>

      {createOpen && config && (
        <FilterModal
          config={config}
          filter={null}
          onClose={() => setCreateOpen(false)}
          onSaved={() => { handleRefresh(); fetchResults() }}
        />
      )}

      <Toast />
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react'
import type { VacancyFilter, Stats, AppConfig, VacancyResult, SavedVacancy, BlocklistItem, ParserStatus } from './types'
import { api } from './api'
import Tabs from './components/Tabs'
import FiltersPanel from './components/FiltersPanel'
import ResultsPanel from './components/ResultsPanel'
import HistoryPanel from './components/HistoryPanel'
import StatsPanel from './components/StatsPanel'
import SavedPanel from './components/SavedPanel'
import BlocklistPanel from './components/BlocklistPanel'
import StatusBar from './components/StatusBar'
import FilterModal from './components/FilterModal'
import Toast, { toast } from './components/Toast'

const TABS = [
  { key: 'search', label: '🔍 Поиск' },
  { key: 'history', label: '📨 История' },
  { key: 'saved', label: '📁 Избранное' },
  { key: 'stats', label: '📊 Статистика' },
]

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
    } catch { toast.error('Ошибка загрузки результатов') }
  }, [])

  const fetchSaved = useCallback(async () => {
    try { setSaved(await api.getSaved()) } catch { toast.error('Ошибка загрузки избранного') }
  }, [])

  const fetchBlocklist = useCallback(async () => {
    try { setBlocklist(await api.getBlocklist()) } catch { toast.error('Ошибка загрузки блок-листа') }
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
    } catch { toast.error('Ошибка запуска проверки') }
    finally { setCheckingNow(false) }
  }

  const handleRefresh = useCallback(() => {
    fetchFilters()
    fetchResults()
    fetchStats()
    fetchSaved()
    fetchBlocklist()
  }, [fetchFilters, fetchResults, fetchStats, fetchSaved, fetchBlocklist])

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <div className="max-w-6xl mx-auto px-4 py-5">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3 mb-2">
          <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">🔍 Job Bot</h1>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setCreateOpen(true); setSelectedFilterId(null) }}
              className="px-3 py-1.5 text-xs font-medium border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
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

        {/* Status bar */}
        <StatusBar status={status} />

        {/* Tabs */}
        <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />

        {/* Search tab */}
        {activeTab === 'search' && config && (
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-3.5">
              <FiltersPanel
                filters={filters}
                config={config}
                selectedId={selectedFilterId}
                onSelect={setSelectedFilterId}
                onRefresh={handleRefresh}
              />
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleCheckNow}
                disabled={checkingNow}
                className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-xl hover:bg-primary-hover disabled:opacity-50 transition-all cursor-pointer shadow-sm"
              >
                {checkingNow || checking ? '⏳ Проверка...' : '🔍 Проверить сейчас'}
              </button>
              <button
                onClick={fetchResults}
                className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-xl hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
              >
                🔄 Обновить
              </button>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <ResultsPanel
                results={results}
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

        {/* History */}
        {activeTab === 'history' && config && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <HistoryPanel config={config} />
          </div>
        )}

        {/* Saved tab */}
        {activeTab === 'saved' && config && (
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">📌 Сохранённые вакансии</h2>
              <SavedPanel saved={saved} config={config} />
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
              <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">🚫 Блок-лист</h2>
              <BlocklistPanel items={blocklist} onRefresh={fetchBlocklist} />
            </div>
          </div>
        )}

        {/* Stats */}
        {activeTab === 'stats' && stats && <StatsPanel stats={stats} />}

        {!config && (
          <div className="text-center py-20 text-gray-400"><p>Загрузка...</p></div>
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

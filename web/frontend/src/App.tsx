import { useState, useEffect, useCallback } from 'react'
import type { VacancyFilter, HistoryItem, Stats, AppConfig, VacancyResult } from './types'
import { api } from './api'
import Tabs from './components/Tabs'
import FiltersPanel from './components/FiltersPanel'
import HistoryPanel from './components/HistoryPanel'
import StatsPanel from './components/StatsPanel'
import ResultsPanel from './components/ResultsPanel'
import FilterModal from './components/FilterModal'
import Toast from './components/Toast'
import { toast } from './components/Toast'

const TABS = [
  { key: 'results', label: '🔍 Результаты' },
  { key: 'filters', label: '📋 Фильтры' },
  { key: 'history', label: '📨 История' },
  { key: 'stats', label: '📊 Статистика' },
]

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [filters, setFilters] = useState<VacancyFilter[]>([])
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [results, setResults] = useState<VacancyResult[]>([])
  const [checkedAt, setCheckedAt] = useState<string | null>(null)
  const [resultsLoading, setResultsLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('results')
  const [createOpen, setCreateOpen] = useState(false)
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  const toggleTheme = useCallback(() => setDark((prev) => !prev), [])

  const fetchConfig = useCallback(async () => {
    try {
      const c = await api.getConfig()
      setConfig(c)
    } catch {
      console.error('Failed to load config')
    }
  }, [])

  const fetchFilters = useCallback(async () => {
    try {
      const data = await api.getFilters()
      setFilters(data)
    } catch {
      toast.error('Ошибка загрузки фильтров')
    }
  }, [])

  const fetchHistory = useCallback(async () => {
    try {
      const data = await api.getHistory()
      setHistory(data)
    } catch {
      toast.error('Ошибка загрузки истории')
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const data = await api.getStats()
      setStats(data)
    } catch {
      toast.error('Ошибка загрузки статистики')
    }
  }, [])

  const fetchResults = useCallback(async () => {
    setResultsLoading(true)
    try {
      const data = await api.getResults()
      setResults(data.items)
      setCheckedAt(data.checked_at)
    } catch {
      toast.error('Ошибка загрузки результатов')
    } finally {
      setResultsLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchConfig()
  }, [fetchConfig])

  useEffect(() => {
    if (activeTab === 'results') fetchResults()
    else if (activeTab === 'filters') fetchFilters()
    else if (activeTab === 'history') fetchHistory()
    else if (activeTab === 'stats') fetchStats()
  }, [activeTab, fetchResults, fetchFilters, fetchHistory, fetchStats])

  useEffect(() => {
    const timer = setInterval(() => {
      if (activeTab === 'results') fetchResults()
      else if (activeTab === 'filters' && !createOpen) fetchFilters()
      else if (activeTab === 'history') fetchHistory()
      else if (activeTab === 'stats') fetchStats()
    }, 30000)
    return () => clearInterval(timer)
  }, [activeTab, createOpen, fetchResults, fetchFilters, fetchHistory, fetchStats])

  const handleCheckNow = async () => {
    setChecking(true)
    try {
      const result = await api.checkNow()
      toast.success(result.message || 'Проверка запущена!')
    } catch {
      toast.error('Ошибка запуска проверки')
    } finally {
      setChecking(false)
    }
  }

  const handleRefresh = useCallback(() => {
    fetchFilters()
    fetchHistory()
    fetchStats()
    fetchResults()
  }, [fetchFilters, fetchHistory, fetchStats, fetchResults])

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold">
              🔍 Job Bot
              <span className="text-sm font-normal text-gray-500 dark:text-gray-400 ml-2">
                Панель управления фильтрами
              </span>
            </h1>
          </div>
          <button
            onClick={toggleTheme}
            className="px-3 py-1.5 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            aria-label={dark ? 'Светлая тема' : 'Тёмная тема'}
          >
            {dark ? '☀️' : '🌙'}
          </button>
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-2 mb-4">
          <button
            onClick={handleCheckNow}
            disabled={checking}
            className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 cursor-pointer"
            aria-label="Проверить вакансии сейчас"
          >
            {checking ? '⏳ Проверка...' : '🔍 Проверить сейчас'}
          </button>
          <button
            onClick={() => {
              setCreateOpen(true)
              setActiveTab('filters')
            }}
            className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer"
            aria-label="Создать фильтр"
          >
            ➕ Создать фильтр
          </button>
          <span className="text-xs text-gray-400 self-center ml-2">
            Автоматически раз в час · обновление каждые 30 с
          </span>
        </div>

        {/* Tabs */}
        <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />

        {/* Panels */}
        {activeTab === 'results' && config && (
          <ResultsPanel
            results={results}
            config={config}
            checkedAt={checkedAt}
            loading={resultsLoading}
          />
        )}

        {activeTab === 'filters' && config && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <FiltersPanel filters={filters} config={config} onRefresh={handleRefresh} />
          </div>
        )}

        {activeTab === 'history' && config && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
            <HistoryPanel history={history} config={config} />
          </div>
        )}

        {activeTab === 'stats' && stats && (
          <StatsPanel stats={stats} />
        )}

        {!config && (
          <div className="text-center py-20 text-gray-400">
            <p>Загрузка...</p>
          </div>
        )}
      </div>

      {/* Create modal */}
      {createOpen && config && (
        <FilterModal
          config={config}
          filter={null}
          onClose={() => setCreateOpen(false)}
          onSaved={handleRefresh}
        />
      )}

      <Toast />
    </div>
  )
}

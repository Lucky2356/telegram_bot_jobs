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
import LoginPage from './components/LoginPage'

const TABS = [
  { key: 'search', label: 'Поиск' },
  { key: 'history', label: 'История' },
  { key: 'saved', label: 'Избранное' },
  { key: 'stats', label: 'Статистика' },
]

const loadingSpinner = (
  <div className="text-center py-20 text-slate-400">
    <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent" />
    <p className="mt-3 text-sm">Загрузка...</p>
  </div>
)

function AuthGate({ onLogin }: { onLogin: (token: string) => void }) {
  const [authState, setAuthState] = useState<'loading' | 'login' | 'done'>(() =>
    sessionStorage.getItem('auth_token') ? 'done' : 'loading'
  )

  useEffect(() => {
    if (authState !== 'loading') return
    // Auto-login for backward compat (без WEB_PASSWORD)
    fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: '' }),
    })
      .then((r) => r.json())
      .then((data) => {
        if (data.ok && data.token) {
          sessionStorage.setItem('auth_token', data.token)
          onLogin(data.token)
          setAuthState('done')
        } else {
          setAuthState('login')
        }
      })
      .catch(() => setAuthState('login'))
  }, [authState, onLogin])

  if (authState === 'loading') return loadingSpinner
  if (authState === 'login') return <LoginPage onLogin={(t) => { onLogin(t); setAuthState('done') }} />
  return null
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('auth_token'))

  const handleLogin = (newToken: string) => {
    sessionStorage.setItem('auth_token', newToken)
    setToken(newToken)
  }

  if (!token) {
    return <AuthGate onLogin={handleLogin} />
  }

  return (
    <ErrorBoundary>
      <AuthenticatedApp />
    </ErrorBoundary>
  )
}

function AuthenticatedApp() {
  const [config, setConfig] = useState<AppConfig | null>(null)
  const [configError, setConfigError] = useState(false)
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
  const [checkingNow, setCheckingNow] = useState(false)
  const [currentFilter, setCurrentFilter] = useState<string | null>(null)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    try { localStorage.setItem('theme', dark ? 'dark' : 'light') } catch { /* ignore */ }
  }, [dark])

  const fetchConfig = useCallback(async () => {
    try {
      setConfig(await api.getConfig())
      setConfigError(false)
    } catch {
      setConfigError(true)
      toast.error('Не удалось загрузить конфигурацию. Проверьте подключение к серверу.')
    }
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

  // SSE для real-time обновлений
  useEffect(() => {
    const es = new EventSource('/api/events')
    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        switch (event.type) {
          case 'check_started':
            setChecking(true)
            setCurrentFilter(null)
            break
          case 'filter_started':
            setCurrentFilter(event.filter_name)
            break
          case 'filter_done':
            break
          case 'sending_started':
            setCurrentFilter(null)
            break
          case 'check_complete':
            setChecking(false)
            setCurrentFilter(null)
            fetchResults()
            break
        }
      } catch { /* ignore */ }
    }
    return () => es.close()
  }, [fetchResults])

  const toggleTheme = () => setDark((prev) => !prev)

  const handleCheckNow = async () => {
    setCheckingNow(true)
    try {
      await api.checkNow()
      toast.success('Проверка запущена!')
      setChecking(true)
    } catch { toast.error('Ошибка') }
    finally { setCheckingNow(false) }
  }

  const handleRefresh = useCallback(() => {
    fetchFilters(); fetchResults(); fetchStats(); fetchSaved(); fetchBlocklist()
  }, [fetchFilters, fetchResults, fetchStats, fetchSaved, fetchBlocklist])

  const handleCloseFilter = useCallback(() => setCreateOpen(false), [])
  const handleSavedFilter = useCallback(() => { handleRefresh() }, [handleRefresh])

  const pageTitle = TABS.find((t) => t.key === activeTab)?.label || ''

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex flex-col w-56 shrink-0 border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
        <div className="p-4 border-b border-slate-200 dark:border-slate-800">
          <h1 className="text-lg font-bold text-slate-950 dark:text-white tracking-tight">Job Bot</h1>
        </div>
        <div className="flex-1 p-3">
          <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />
        </div>
        <div className="p-3 border-t border-slate-200 dark:border-slate-800">
          <StatusBar status={status} />
          <button
            onClick={toggleTheme}
            className="mt-2 w-full px-3 py-2 text-xs font-medium text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors cursor-pointer flex items-center gap-2"
            aria-label={dark ? 'Светлая тема' : 'Тёмная тема'}
          >
            {dark ? '☀️' : '🌙'} {dark ? 'Светлая' : 'Тёмная'}
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800 px-4 md:px-6 py-3 flex items-center justify-between gap-3">
          {/* Mobile: sidebar toggle + title */}
          <div className="flex items-center gap-3 md:hidden">
            <h1 className="text-base font-bold text-slate-950 dark:text-white tracking-tight">Job Bot</h1>
            <StatusBar status={status} />
          </div>
          <div className="hidden md:flex items-center gap-3">
            <h2 className="text-lg font-semibold text-slate-950 dark:text-white tracking-tight">{pageTitle}</h2>
            <StatusBar status={status} />
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setCreateOpen(true); setSelectedFilterId(null) }}
              className="px-3.5 py-2 text-xs font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:scale-[0.98] transition-all cursor-pointer"
            >
              ➕ Фильтр
            </button>
            <button
              onClick={toggleTheme}
              className="md:hidden px-3 py-2 text-xs border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-slate-500 dark:text-slate-400 transition-colors"
              aria-label={dark ? 'Светлая тема' : 'Тёмная тема'}
            >
              {dark ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Mobile tabs */}
        <div className="md:hidden px-4 pt-3 pb-1 bg-white dark:bg-slate-950 border-b border-slate-200 dark:border-slate-800">
          <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} />
        </div>

        {/* Content */}
        <div className="flex-1 px-4 md:px-6 py-5">
          {activeTab === 'search' && config && (
            <ErrorBoundary>
              <div className="space-y-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-4">
                  <FiltersPanel filters={filters} config={config} selectedId={selectedFilterId} onSelect={setSelectedFilterId} onRefresh={handleRefresh} />
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCheckNow}
                    disabled={checkingNow}
                    className="px-5 py-2.5 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer shadow-sm"
                  >
                    {checkingNow || checking ? (currentFilter ? `⏳ ${currentFilter}` : '⏳ Проверка...') : '🔍 Проверить сейчас'}
                  </button>
                  <button
                    onClick={fetchResults}
                    className="px-4 py-2.5 text-sm border border-slate-200 dark:border-slate-700 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer text-slate-500 dark:text-slate-400 transition-colors"
                  >
                    🔄 Обновить
                  </button>
                </div>

                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-4">
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
              <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-4">
                <HistoryPanel config={config} />
              </div>
            </ErrorBoundary>
          )}

          {activeTab === 'saved' && config && (
            <ErrorBoundary>
              <div className="space-y-4">
                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-4">
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">📌 Сохранённые вакансии</h2>
                  <SavedPanel saved={saved} config={config} onRefresh={fetchSaved} />
                </div>
                <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-800 p-4">
                  <h2 className="text-sm font-semibold text-slate-900 dark:text-slate-100 mb-3">🚫 Блок-лист</h2>
                  <BlocklistPanel items={blocklist} onRefresh={fetchBlocklist} />
                </div>
              </div>
            </ErrorBoundary>
          )}

          {activeTab === 'stats' && (stats ? (
            <ErrorBoundary>
              <Suspense fallback={<div className="text-center py-20 text-slate-400"><p className="text-sm">Загрузка графиков...</p></div>}>
                <StatsPanel stats={stats} />
              </Suspense>
            </ErrorBoundary>
          ) : loadingSpinner)}

          {!config && !configError && loadingSpinner}
          {configError && (
            <div className="text-center py-20 text-slate-400">
              <p className="mb-3">Не удалось загрузить данные</p>
              <button onClick={fetchConfig} className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer">
                Повторить
              </button>
            </div>
          )}
        </div>
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

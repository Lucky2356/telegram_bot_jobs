import { useState, useEffect, useCallback, lazy, Suspense, useMemo } from 'react'
import {
  MoonStar,
  Sun,
  MonitorCog,
  Plus,
  SearchCheck,
  Filter,
  BellRing,
  LayoutGrid,
} from 'lucide-react'
import type {
  VacancyFilter,
  Stats,
  AppConfig,
  VacancyResult,
  SavedVacancy,
  BlocklistItem,
  ParserStatus,
} from './types'
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
import Toast from './components/Toast'
import { toast } from './components/toastBus'
import LoginPage from './components/LoginPage'

type ThemeMode = 'light' | 'dark' | 'system'

interface TelegramWebAppLike {
  ready?: () => void
  expand?: () => void
  themeParams?: Record<string, string | undefined>
  onEvent?: (eventName: string, callback: () => void) => void
}

const TABS = [
  { key: 'search', label: 'Поиск', shortLabel: 'Поиск', icon: 'search' },
  { key: 'history', label: 'История', shortLabel: 'История', icon: 'history' },
  { key: 'saved', label: 'Избранное', shortLabel: 'Сейвы', icon: 'saved' },
  { key: 'stats', label: 'Аналитика', shortLabel: 'Метрики', icon: 'stats' },
]

const loadingSpinner = (
  <div className="bento-card p-8 text-center text-secondary">
    <div className="mx-auto mb-3 h-8 w-8 animate-spin rounded-full border-2 border-[var(--accent)] border-r-transparent" />
    <p className="text-sm">Загружаем данные...</p>
  </div>
)

function AuthGate({ onLogin }: { onLogin: (token: string) => void }) {
  const [authState, setAuthState] = useState<'loading' | 'login' | 'done'>(() =>
    sessionStorage.getItem('auth_token') ? 'done' : 'loading',
  )

  useEffect(() => {
    if (authState !== 'loading') return
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
          return
        }
        setAuthState('login')
      })
      .catch(() => setAuthState('login'))
  }, [authState, onLogin])

  if (authState === 'loading') return loadingSpinner
  if (authState === 'login') return <LoginPage onLogin={(t) => { onLogin(t); setAuthState('done') }} />
  return null
}

function resolveSystemDark() {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme(mode: ThemeMode) {
  const html = document.documentElement
  const dark = mode === 'dark' || (mode === 'system' && resolveSystemDark())
  html.classList.toggle('dark', dark)
  html.dataset.theme = dark ? 'dark' : 'light'
}

function applyTelegramThemeParams(themeParams: Record<string, string | undefined>) {
  const html = document.documentElement
  const map: Record<string, string | undefined> = {
    '--bg': themeParams.bg_color,
    '--surface-strong': themeParams.secondary_bg_color,
    '--text-primary': themeParams.text_color,
    '--text-muted': themeParams.hint_color,
    '--accent': themeParams.button_color,
  }

  for (const [cssVar, value] of Object.entries(map)) {
    if (!value) continue
    html.style.setProperty(cssVar, value)
  }
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem('auth_token'))

  const handleLogin = useCallback((newToken: string) => {
    sessionStorage.setItem('auth_token', newToken)
    setToken(newToken)
  }, [])

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
  const [themeMode, setThemeMode] = useState<ThemeMode>(() => {
    try {
      const stored = localStorage.getItem('theme_mode')
      if (stored === 'dark' || stored === 'light' || stored === 'system') return stored
    } catch {
      // ignore
    }
    return 'system'
  })
  const [checkingNow, setCheckingNow] = useState(false)
  const [currentFilter, setCurrentFilter] = useState<string | null>(null)

  useEffect(() => {
    applyTheme(themeMode)
    try {
      localStorage.setItem('theme_mode', themeMode)
    } catch {
      // ignore
    }

    if (themeMode !== 'system') return

    const media = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = () => applyTheme('system')
    media.addEventListener('change', handler)
    return () => media.removeEventListener('change', handler)
  }, [themeMode])

  useEffect(() => {
    const tg = (window as { Telegram?: { WebApp?: TelegramWebAppLike } }).Telegram?.WebApp
    if (!tg) return

    try {
      tg.ready?.()
      tg.expand?.()
      if (tg.themeParams) applyTelegramThemeParams(tg.themeParams)
      if (typeof tg.onEvent === 'function') {
        tg.onEvent('themeChanged', () => {
          if (tg.themeParams) applyTelegramThemeParams(tg.themeParams)
        })
      }
    } catch {
      // ignore telegram sdk errors
    }
  }, [])

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
    try {
      setStatus(await api.getStatus())
    } catch {
      // ignore
    }
  }, [])

  const fetchFilters = useCallback(async () => {
    try {
      setFilters(await api.getFilters())
    } catch {
      toast.error('Ошибка загрузки фильтров')
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      setStats(await api.getStats())
    } catch {
      toast.error('Ошибка загрузки статистики')
    }
  }, [])

  const fetchResults = useCallback(async () => {
    try {
      const data = await api.getResults()
      setResults(data.items)
      setCheckedAt(data.checked_at)
      setChecking(data.checking)
    } catch {
      // ignore
    }
  }, [])

  const fetchSaved = useCallback(async () => {
    try {
      setSaved(await api.getSaved())
    } catch {
      // ignore
    }
  }, [])

  const fetchBlocklist = useCallback(async () => {
    try {
      setBlocklist(await api.getBlocklist())
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    void fetchConfig()
    void fetchStatus()
  }, [fetchConfig, fetchStatus])

  useEffect(() => {
    if (activeTab === 'search') {
      void fetchFilters()
      void fetchResults()
    } else if (activeTab === 'saved') {
      void fetchSaved()
      void fetchBlocklist()
    } else if (activeTab === 'stats') {
      void fetchStats()
    }
  }, [activeTab, fetchFilters, fetchResults, fetchSaved, fetchBlocklist, fetchStats])

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
          case 'sending_started':
            setCurrentFilter(null)
            break
          case 'check_complete':
            setChecking(false)
            setCurrentFilter(null)
            void fetchResults()
            break
          default:
            break
        }
      } catch {
        // ignore
      }
    }
    es.onerror = () => {
      setChecking(false)
      setCurrentFilter(null)
    }
    return () => es.close()
  }, [fetchResults])

  const cycleTheme = () => {
    setThemeMode((prev) => {
      if (prev === 'system') return 'light'
      if (prev === 'light') return 'dark'
      return 'system'
    })
  }

  const themeMeta = {
    system: { icon: <MonitorCog className="h-4 w-4" />, label: 'Система' },
    light: { icon: <Sun className="h-4 w-4" />, label: 'Светлая' },
    dark: { icon: <MoonStar className="h-4 w-4" />, label: 'Тёмная' },
  }[themeMode]

  const handleCheckNow = async () => {
    setCheckingNow(true)
    try {
      await api.checkNow()
      toast.success('Проверка запущена')
      setChecking(true)
    } catch {
      toast.error('Ошибка запуска проверки')
    } finally {
      setCheckingNow(false)
    }
  }

  const handleRefresh = useCallback(() => {
    void fetchFilters()
    void fetchResults()
    void fetchStats()
    void fetchSaved()
    void fetchBlocklist()
  }, [fetchFilters, fetchResults, fetchStats, fetchSaved, fetchBlocklist])

  const handleCloseFilter = useCallback(() => setCreateOpen(false), [])
  const handleSavedFilter = useCallback(() => { handleRefresh() }, [handleRefresh])

  const pageTitle = TABS.find((t) => t.key === activeTab)?.label || ''
  const activeFilters = useMemo(() => filters.filter((f) => f.active).length, [filters])
  const latestResultTitle = results[0]?.title

  return (
    <div className="min-h-screen text-primary">
      <div className="mx-auto flex min-h-screen w-full max-w-[1680px]">
        <aside className="hidden w-72 shrink-0 border-r border-[var(--border)] bg-[color:var(--surface)]/80 px-5 pb-6 pt-5 backdrop-blur xl:flex xl:flex-col">
          <div className="mb-6 flex items-center gap-3 px-1">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl accent-gradient text-white shadow-[var(--shadow-sm)]">
              <LayoutGrid className="h-5 w-5" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-wide text-secondary">Платформа вакансий</p>
              <h1 className="text-xl font-bold tracking-tight">Поиск и аналитика</h1>
            </div>
          </div>

          <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} variant="sidebar" />

          <div className="mt-auto space-y-3 rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Статус источников</p>
            <StatusBar status={status} compact />
            <button
              onClick={cycleTheme}
              className="focus-ring flex h-10 w-full items-center justify-center gap-2 rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] text-sm font-medium text-secondary transition hover:border-[var(--border-strong)] hover:text-primary"
              aria-label="Сменить тему"
            >
              {themeMeta.icon}
              <span className="btn-text">{themeMeta.label}</span>
            </button>
          </div>
        </aside>

        <main className="flex min-h-screen min-w-0 flex-1 flex-col pb-20 xl:pb-6">
          <header className="sticky top-0 z-30 border-b border-[var(--border)] bg-[color:var(--surface)]/88 px-4 py-3 backdrop-blur md:px-6">
            <div className="mx-auto flex w-full items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Рабочая область</p>
                <div className="mt-0.5 flex items-center gap-2">
                  <h2 className="text-lg font-semibold tracking-tight md:text-2xl">{pageTitle}</h2>
                  <span className="hidden rounded-full border border-[var(--border)] bg-[color:var(--surface-elevated)] px-2.5 py-1 text-[11px] font-medium text-secondary md:inline-flex">
                    Активная вкладка
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={cycleTheme}
                  className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm font-medium text-secondary transition hover:border-[var(--border-strong)] hover:text-primary xl:hidden"
                  aria-label="Сменить тему"
                >
                  {themeMeta.icon}
                  <span className="btn-text hidden sm:inline">{themeMeta.label}</span>
                </button>

                <button
                  onClick={() => {
                    setCreateOpen(true)
                    setSelectedFilterId(null)
                  }}
                  className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
                >
                  <Plus className="h-4 w-4" />
                  <span className="btn-text">Новый фильтр</span>
                </button>
              </div>
            </div>
          </header>

          <div className="px-4 py-4 md:px-6 md:py-6">
            {activeTab === 'search' && config && (
              <ErrorBoundary>
                <section className="space-y-4">
                  <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
                    <article className="bento-card animate-soft-scale p-4 lg:col-span-3">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Активные фильтры</p>
                      <p className="mt-2 text-3xl font-bold tracking-tight text-primary code">{activeFilters}</p>
                      <p className="mt-1 text-xs text-secondary">Всего фильтров: {filters.length}</p>
                    </article>
                    <article className="bento-card animate-soft-scale p-4 lg:col-span-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Последний поиск</p>
                      <p className="mt-2 line-clamp-2 text-sm font-medium text-primary">
                        {latestResultTitle || 'Пока нет результатов. Запустите проверку и соберите первую выдачу.'}
                      </p>
                      {checkedAt && (
                        <p className="mt-2 text-xs text-secondary">
                          Обновлено {new Date(checkedAt).toLocaleString('ru-RU', {
                            day: '2-digit',
                            month: 'short',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      )}
                    </article>
                    <article className="bento-card animate-soft-scale p-4 lg:col-span-5">
                      <div className="flex h-full flex-col justify-between gap-3">
                        <div className="flex items-center justify-between gap-2">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Проверка вакансий</p>
                            <p className="mt-1 text-sm text-secondary">
                              {checking
                                ? currentFilter
                                  ? `Сканируем фильтр: ${currentFilter}`
                                  : 'Идёт проверка источников...'
                                : 'Готово к запуску новой проверки'}
                            </p>
                          </div>
                          {checking ? (
                            <span className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--accent-soft)] px-3 py-1 text-xs font-medium text-primary">
                              <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--accent)]" />
                              В процессе
                            </span>
                          ) : (
                            <SearchCheck className="h-5 w-5 text-[var(--accent)]" />
                          )}
                        </div>
                        <button
                          onClick={handleCheckNow}
                          disabled={checkingNow}
                          className="focus-ring inline-flex h-11 items-center justify-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-50"
                        >
                          <BellRing className="h-4 w-4" />
                          {checkingNow || checking ? 'Проверяем...' : 'Проверить сейчас'}
                        </button>
                      </div>
                    </article>
                  </div>

                  <div className="grid grid-cols-1 gap-4 xl:grid-cols-12">
                    <section className="bento-card xl:col-span-4">
                      <div className="flex items-center justify-between border-b border-[var(--border)] px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Filter className="h-4 w-4 text-secondary" />
                          <h3 className="text-sm font-semibold text-primary">Панель фильтров</h3>
                        </div>
                      </div>
                      <div className="p-4">
                        <FiltersPanel
                          filters={filters}
                          config={config}
                          selectedId={selectedFilterId}
                          onSelect={setSelectedFilterId}
                          onRefresh={handleRefresh}
                        />
                      </div>
                    </section>

                    <section className="bento-card xl:col-span-8">
                      <div className="border-b border-[var(--border)] px-4 py-3">
                        <h3 className="text-sm font-semibold text-primary">Лента вакансий</h3>
                      </div>
                      <div className="p-4">
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
                    </section>
                  </div>
                </section>
              </ErrorBoundary>
            )}

            {activeTab === 'history' && config && (
              <ErrorBoundary>
                <section className="bento-card p-4 md:p-5">
                  <HistoryPanel config={config} />
                </section>
              </ErrorBoundary>
            )}

            {activeTab === 'saved' && config && (
              <ErrorBoundary>
                <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
                  <article className="bento-card xl:col-span-8">
                    <div className="border-b border-[var(--border)] px-4 py-3">
                      <h3 className="text-sm font-semibold text-primary">Сохранённые вакансии</h3>
                    </div>
                    <div className="p-4">
                      <SavedPanel saved={saved} config={config} onRefresh={fetchSaved} />
                    </div>
                  </article>

                  <article className="bento-card xl:col-span-4">
                    <div className="border-b border-[var(--border)] px-4 py-3">
                      <h3 className="text-sm font-semibold text-primary">Блок-лист</h3>
                    </div>
                    <div className="p-4">
                      <BlocklistPanel items={blocklist} onRefresh={fetchBlocklist} />
                    </div>
                  </article>
                </section>
              </ErrorBoundary>
            )}

            {activeTab === 'stats' && (
              stats ? (
                <ErrorBoundary>
                  <Suspense fallback={loadingSpinner}>
                    <StatsPanel stats={stats} />
                  </Suspense>
                </ErrorBoundary>
              ) : loadingSpinner
            )}

            {!config && !configError && loadingSpinner}
            {configError && (
              <div className="bento-card p-8 text-center">
                <p className="text-base font-medium text-primary">Не удалось загрузить данные</p>
                <p className="mt-2 text-sm text-secondary">Проверьте backend и повторите запрос.</p>
                <button
                  onClick={fetchConfig}
                  className="focus-ring mt-4 inline-flex h-10 items-center justify-center rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
                >
                  Повторить
                </button>
              </div>
            )}
          </div>
        </main>
      </div>

      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-[var(--border)] bg-[color:var(--surface)]/92 px-3 py-2 backdrop-blur xl:hidden">
        <Tabs tabs={TABS} active={activeTab} onTabChange={setActiveTab} variant="bottom" />
      </div>

      {createOpen && config && (
        <ErrorBoundary>
          <FilterModal
            key="create-filter"
            config={config}
            filter={null}
            onClose={handleCloseFilter}
            onSaved={handleSavedFilter}
          />
        </ErrorBoundary>
      )}

      <Toast />
    </div>
  )
}

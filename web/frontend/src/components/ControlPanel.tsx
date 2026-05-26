import { useMemo, useState } from 'react'
import { Activity, Archive, Download, FileUp, Microscope, RefreshCw, SearchCheck, Send } from 'lucide-react'
import type {
  AppConfig,
  BackupItem,
  ConfigDiagnostics,
  DeliveryStatus,
  DeliveryItem,
  EventLogItem,
  FilterDiagnostics,
  FilterRecommendation,
  FilterPerformanceItem,
  FilterFormData,
  ParserHealthItem,
  TaskStatus,
  VacancyFilter,
  VacancyResult,
} from '../types'
import { api } from '../api'
import { toast } from './toastBus'
import VacancyCard from './VacancyCard'

interface ControlPanelProps {
  filters: VacancyFilter[]
  config: AppConfig
  onRefresh: () => void
}

const rejectLabels: Record<string, string> = {
  keyword: 'Ключевые слова',
  noise: 'Шум/нерелевантно',
  exclude: 'Исключения',
  employment: 'Занятость',
  city: 'Город',
  experience: 'Опыт',
  salary: 'Зарплата',
  blocklist: 'Блок-лист',
}

export default function ControlPanel({ filters, config, onRefresh }: ControlPanelProps) {
  const [selectedId, setSelectedId] = useState<number | ''>(filters[0]?.id ?? '')
  const [diagnostics, setDiagnostics] = useState<FilterDiagnostics | null>(null)
  const [preview, setPreview] = useState<VacancyResult[]>([])
  const [health, setHealth] = useState<ParserHealthItem[]>([])
  const [logs, setLogs] = useState<EventLogItem[]>([])
  const [delivery, setDelivery] = useState<DeliveryStatus | null>(null)
  const [deliveries, setDeliveries] = useState<DeliveryItem[]>([])
  const [backups, setBackups] = useState<BackupItem[]>([])
  const [performance, setPerformance] = useState<FilterPerformanceItem[]>([])
  const [configDiagnostics, setConfigDiagnostics] = useState<ConfigDiagnostics | null>(null)
  const [recommendations, setRecommendations] = useState<FilterRecommendation[]>([])
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [importText, setImportText] = useState('')
  const [busy, setBusy] = useState<string | null>(null)

  const selectedFilter = useMemo(
    () => filters.find((filter) => filter.id === selectedId),
    [filters, selectedId],
  )

  const selectedFilterId = typeof selectedId === 'number' ? selectedId : null

  const runDiagnostics = async () => {
    if (!selectedFilterId) return
    setBusy('diagnostics')
    try {
      setDiagnostics(await api.diagnoseFilter(selectedFilterId))
      toast.success('Диагностика готова')
    } catch {
      toast.error('Не удалось выполнить диагностику')
    } finally {
      setBusy(null)
    }
  }

  const loadRecommendations = async () => {
    if (!selectedFilterId) return
    setBusy('recommendations')
    try {
      const data = await api.getFilterRecommendations(selectedFilterId)
      setRecommendations(data.recommendations)
      toast.success(`Рекомендаций: ${data.recommendations.length}`)
    } catch {
      toast.error('Не удалось получить рекомендации')
    } finally {
      setBusy(null)
    }
  }

  const runPreview = async () => {
    if (!selectedFilterId) return
    setBusy('preview')
    try {
      const data = await api.previewFilter(selectedFilterId)
      setPreview(data.items)
      toast.success(`Preview: ${data.items.length} вакансий`)
    } catch {
      toast.error('Не удалось запустить preview')
    } finally {
      setBusy(null)
    }
  }

  const refreshHealth = async () => {
    setBusy('health')
    try {
      setHealth(await api.getParserHealth())
    } catch {
      toast.error('Не удалось проверить источники')
    } finally {
      setBusy(null)
    }
  }

  const refreshLogs = async () => {
    setBusy('logs')
    try {
      setLogs(await api.getEventLogs())
    } catch {
      toast.error('Не удалось загрузить журнал')
    } finally {
      setBusy(null)
    }
  }

  const refreshOps = async () => {
    setBusy('ops')
    try {
      const [deliveryData, performanceData, healthHistory, diagnosticsData, taskData] = await Promise.all([
        api.getDeliveryStatus(),
        api.getFilterPerformance(),
        api.getParserHealthHistory(),
        api.getConfigDiagnostics(),
        api.getTaskStatus(),
      ])
      setDelivery(deliveryData)
      setPerformance(performanceData)
      setConfigDiagnostics(diagnosticsData)
      setTaskStatus(taskData)
      if (healthHistory.length > 0) setHealth(healthHistory)
    } catch {
      toast.error('Не удалось загрузить операционные данные')
    } finally {
      setBusy(null)
    }
  }

  const refreshDeliveries = async () => {
    setBusy('deliveries')
    try {
      const [status, recent] = await Promise.all([
        api.getDeliveryStatus(),
        api.getRecentDeliveries(),
      ])
      setDelivery(status)
      setDeliveries(recent)
    } catch {
      toast.error('Не удалось загрузить доставки Telegram')
    } finally {
      setBusy(null)
    }
  }

  const retryDelivery = async () => {
    setBusy('retry-delivery')
    try {
      const status = await api.retryDelivery()
      setDelivery(status)
      setDeliveries(await api.getRecentDeliveries())
      toast.success(`Retry запущен, восстановлено: ${status.restored}`)
    } catch {
      toast.error('Не удалось запустить retry')
    } finally {
      setBusy(null)
    }
  }

  const cleanupDelivery = async () => {
    setBusy('cleanup-delivery')
    try {
      const status = await api.cleanupDelivery()
      setDelivery(status)
      setDeliveries(await api.getRecentDeliveries())
      toast.success(`Очищено записей: ${status.deleted}`)
    } catch {
      toast.error('Не удалось очистить очередь')
    } finally {
      setBusy(null)
    }
  }

  const createBackup = async () => {
    setBusy('backup')
    try {
      const data = await api.createBackup()
      toast.success(`Backup создан: ${data.file}`)
      setBackups(await api.listBackups())
    } catch {
      toast.error('Не удалось создать backup')
    } finally {
      setBusy(null)
    }
  }

  const refreshBackups = async () => {
    setBusy('backups')
    try {
      setBackups(await api.listBackups())
    } catch {
      toast.error('Не удалось загрузить список backup')
    } finally {
      setBusy(null)
    }
  }

  const exportFullBackup = async () => {
    try {
      const data = await api.exportBackup()
      setImportText(JSON.stringify(data, null, 2))
      toast.success('Полный JSON-экспорт готов в поле ниже')
    } catch {
      toast.error('Не удалось экспортировать backup')
    }
  }

  const exportFilters = async () => {
    try {
      const data = await api.exportFilters()
      setImportText(JSON.stringify(data, null, 2))
      toast.success('Экспорт готов в поле ниже')
    } catch {
      toast.error('Не удалось экспортировать фильтры')
    }
  }

  const importFilters = async () => {
    try {
      const parsed = JSON.parse(importText) as { filters?: FilterFormData[] } | FilterFormData[]
      const filtersToImport = Array.isArray(parsed) ? parsed : parsed.filters
      if (!filtersToImport?.length) {
        toast.error('В JSON не найден список фильтров')
        return
      }
      await api.importFilters(filtersToImport, false)
      toast.success('Фильтры импортированы')
      onRefresh()
    } catch {
      toast.error('Не удалось импортировать фильтры')
    }
  }

  return (
    <div className="space-y-4">
      <section className="bento-card p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Диагностика фильтра</p>
            <h2 className="mt-1 text-base font-semibold text-primary">{selectedFilter?.name || 'Фильтр не выбран'}</h2>
          </div>
          <select
            value={selectedId}
            onChange={(event) => setSelectedId(event.target.value ? Number(event.target.value) : '')}
            className="focus-ring h-10 min-w-64 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary"
          >
            {filters.length === 0 && <option value="">Нет фильтров</option>}
            {filters.map((filter) => (
              <option key={filter.id} value={filter.id}>{filter.name}</option>
            ))}
          </select>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <button
            type="button"
            onClick={runDiagnostics}
            disabled={!selectedFilterId || busy === 'diagnostics'}
            className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white disabled:opacity-50"
          >
            <Microscope className="h-4 w-4" />
            Диагностика
          </button>
          <button
            type="button"
            onClick={runPreview}
            disabled={!selectedFilterId || busy === 'preview'}
            className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-4 text-sm font-semibold text-primary disabled:opacity-50"
          >
            <SearchCheck className="h-4 w-4" />
            Preview без Telegram
          </button>
          <button
            type="button"
            onClick={loadRecommendations}
            disabled={!selectedFilterId || busy === 'recommendations'}
            className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-4 text-sm font-semibold text-primary disabled:opacity-50"
          >
            Рекомендации
          </button>
        </div>

        {recommendations.length > 0 && (
          <div className="mt-4 space-y-2">
            {recommendations.map((item) => (
              <p key={`${item.type}-${item.message}`} className="rounded-xl border border-amber-400/25 bg-amber-500/10 px-3 py-2 text-sm text-amber-100">
                {item.message}
              </p>
            ))}
          </div>
        )}

        {diagnostics && (
          <div className="mt-4 grid grid-cols-1 gap-3 xl:grid-cols-2">
            {diagnostics.sites.map((site) => (
              <article key={site.site} className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3">
                <div className="flex items-center justify-between gap-2">
                  <h3 className="text-sm font-semibold text-primary">{config.sites[site.site] || site.site}</h3>
                  <span className="code text-xs text-secondary">{site.passed}/{site.raw}</span>
                </div>
                <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-secondary">
                  {Object.entries(site.rejected).map(([key, value]) => (
                    <span key={key} className="rounded-lg border border-[var(--border)] px-2 py-1">
                      {rejectLabels[key] || key}: <span className="code text-primary">{value}</span>
                    </span>
                  ))}
                </div>
                {site.samples.length > 0 && (
                  <div className="mt-3 space-y-1 text-xs text-secondary">
                    {site.samples.map((sample) => (
                      <p key={`${site.site}-${sample.title}`} className="truncate">
                        <span className="code text-primary">{sample.score}</span> · {sample.title}
                      </p>
                    ))}
                  </div>
                )}
                {site.error && <p className="mt-2 text-xs text-rose-300">{site.error}</p>}
              </article>
            ))}
          </div>
        )}
      </section>

      {preview.length > 0 && (
        <section className="bento-card p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Preview результатов</p>
          <div className="mt-3 grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {preview.slice(0, 12).map((vacancy) => (
              <VacancyCard key={`${vacancy.source}-${vacancy.url}`} vacancy={vacancy} config={config} />
            ))}
          </div>
        </section>
      )}

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <div className="bento-card p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Здоровье источников</p>
            <button onClick={refreshHealth} className="focus-ring inline-flex h-9 items-center gap-2 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary">
              <Activity className="h-4 w-4" />
              Проверить
            </button>
          </div>
          <div className="mt-3 space-y-2">
            {health.map((item) => (
              <div key={item.site} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 py-2 text-sm">
                <span>{config.sites[item.site] || item.site}</span>
                <span className={item.ok ? 'text-emerald-400' : 'text-rose-300'}>
                  {item.ok ? `${item.count} · ${item.latency_ms}мс` : item.error || 'ошибка'}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bento-card p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Журнал событий</p>
            <button onClick={refreshLogs} className="focus-ring inline-flex h-9 items-center gap-2 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary">
              <RefreshCw className="h-4 w-4" />
              Обновить
            </button>
          </div>
          <div className="mt-3 max-h-72 overflow-y-auto rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3">
            {logs.length === 0 ? (
              <p className="text-sm text-secondary">Событий пока нет.</p>
            ) : (
              <pre className="whitespace-pre-wrap text-xs text-secondary">{JSON.stringify(logs.slice().reverse(), null, 2)}</pre>
            )}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="bento-card p-4">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Telegram очередь</p>
            <div className="flex flex-wrap gap-2">
              <button onClick={refreshDeliveries} className="focus-ring inline-flex h-9 items-center gap-2 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary">
                <Send className="h-4 w-4" />
                Детали
              </button>
              <button onClick={retryDelivery} disabled={busy === 'retry-delivery'} className="focus-ring h-9 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary disabled:opacity-50">
                Retry
              </button>
              <button onClick={cleanupDelivery} disabled={busy === 'cleanup-delivery'} className="focus-ring h-9 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary disabled:opacity-50">
                Очистить
              </button>
            </div>
          </div>
          <div className="mt-3 grid grid-cols-3 gap-2 text-center text-sm">
            <span className="rounded-xl border border-[var(--border)] p-3">
              <b className="block text-lg text-primary">{delivery?.pending ?? 0}</b>
              pending
            </span>
            <span className="rounded-xl border border-[var(--border)] p-3">
              <b className="block text-lg text-emerald-400">{delivery?.sent ?? 0}</b>
              sent
            </span>
            <span className="rounded-xl border border-[var(--border)] p-3">
              <b className="block text-lg text-rose-300">{delivery?.failed ?? 0}</b>
              failed
            </span>
          </div>
          {deliveries.length > 0 && (
            <div className="mt-3 max-h-40 space-y-2 overflow-y-auto text-xs">
              {deliveries.slice(0, 8).map((item) => (
                <div key={item.id} className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 py-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="code text-primary">#{item.id} · {item.source}</span>
                    <span className={item.status === 'sent' ? 'text-emerald-400' : item.status === 'failed' ? 'text-rose-300' : 'text-amber-300'}>
                      {item.status} · {item.attempts}
                    </span>
                  </div>
                  {item.last_error && <p className="mt-1 line-clamp-2 text-rose-300">{item.last_error}</p>}
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bento-card p-4 xl:col-span-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Эффективность фильтров за 30 дней</p>
            <button onClick={refreshOps} disabled={busy === 'ops'} className="focus-ring h-9 rounded-xl border border-[var(--border)] px-3 text-xs font-semibold text-primary disabled:opacity-50">
              Обновить
            </button>
          </div>
          <div className="mt-3 max-h-48 space-y-2 overflow-y-auto">
            {performance.length === 0 ? (
              <p className="text-sm text-secondary">Нажми “Обновить” в блоке очереди, чтобы загрузить аналитику.</p>
            ) : performance.map((item) => (
              <div key={item.filter_id} className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 py-2 text-sm">
                <span className="truncate text-primary">{item.filter_name}</span>
                <span className="code text-secondary">{item.sent_count}</span>
              </div>
            ))}
          </div>
          {configDiagnostics && (
            <div className="mt-4 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Конфигурация</p>
              <p className="mt-2 text-xs text-secondary">
                Auth: {configDiagnostics.auth_enabled ? 'включен' : 'выключен'} · DB: {configDiagnostics.database} · cache: {configDiagnostics.search_cache_seconds}s
              </p>
              {configDiagnostics.warnings.length > 0 && (
                <div className="mt-2 space-y-1">
                  {configDiagnostics.warnings.map((warning) => (
                    <p key={warning.message} className="text-xs text-amber-300">{warning.level}: {warning.message}</p>
                  ))}
                </div>
              )}
            </div>
          )}
          {taskStatus && (
            <div className="mt-3 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3 text-xs text-secondary">
              Очередь проверок: <span className="code text-primary">{taskStatus.queued}</span>
              {' '}· worker: {taskStatus.worker_running ? 'активен' : 'спит'}
              {' '}· checking: {taskStatus.checking ? 'да' : 'нет'}
            </div>
          )}
        </div>
      </section>

      <section className="bento-card p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Импорт / экспорт фильтров</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button onClick={exportFilters} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] px-4 text-sm font-semibold text-primary">
            <Download className="h-4 w-4" />
            Экспорт
          </button>
          <button onClick={importFilters} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white">
            <FileUp className="h-4 w-4" />
            Импорт
          </button>
          <button onClick={createBackup} disabled={busy === 'backup'} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] px-4 text-sm font-semibold text-primary disabled:opacity-50">
            <Archive className="h-4 w-4" />
            Backup БД
          </button>
          <button onClick={exportFullBackup} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] px-4 text-sm font-semibold text-primary">
            <Download className="h-4 w-4" />
            Полный JSON
          </button>
          <button onClick={refreshBackups} disabled={busy === 'backups'} className="focus-ring inline-flex h-10 items-center gap-2 rounded-xl border border-[var(--border)] px-4 text-sm font-semibold text-primary disabled:opacity-50">
            <RefreshCw className="h-4 w-4" />
            Список backup
          </button>
        </div>
        {backups.length > 0 && (
          <div className="mt-3 grid grid-cols-1 gap-2 md:grid-cols-2">
            {backups.slice(0, 6).map((item) => (
              <div key={item.file} className="rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 py-2 text-xs">
                <p className="truncate text-primary">{item.name}</p>
                <p className="text-secondary">{Math.round(item.size / 1024)} КБ · {new Date(item.modified_at).toLocaleString()}</p>
              </div>
            ))}
          </div>
        )}
        <textarea
          value={importText}
          onChange={(event) => setImportText(event.target.value)}
          className="focus-ring mt-3 min-h-48 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-3 font-mono text-xs text-primary"
          placeholder="JSON экспорта или список фильтров"
        />
      </section>
    </div>
  )
}

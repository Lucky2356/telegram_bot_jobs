import { useEffect, useRef } from 'react'
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

export default function ResultsPanel({
  results, config, checkedAt, checking, filters, selectedFilterId, onRefreshResults,
}: ResultsPanelProps) {
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    if (checking) {
      pollRef.current = setInterval(() => {
        onRefreshResults()
      }, 3000)
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [checking, onRefreshResults])

  const selectedFilter = filters.find((f) => f.id === selectedFilterId)

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-3 mb-4">
        <div className="flex items-center gap-3">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            {selectedFilter ? (
              <>🔍 Результаты для <span className="text-primary">{selectedFilter.name}</span></>
            ) : (
              '🔍 Все результаты'
            )}
          </h2>
          {checking && (
            <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium bg-amber-50 dark:bg-amber-900/20 text-amber-600 dark:text-amber-400 rounded-full border border-amber-200 dark:border-amber-800 animate-pulse">
              <span className="w-1.5 h-1.5 bg-amber-500 rounded-full animate-ping" />
              Проверка...
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {checkedAt && !checking && (
            <span className="text-[11px] text-gray-400 dark:text-gray-500">
              {new Date(checkedAt).toLocaleString('ru-RU', {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
              })}
            </span>
          )}
          <span className="text-xs font-medium text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2.5 py-1 rounded-full">
            {results.length} {results.length === 1 ? 'вакансия' : results.length < 5 ? 'вакансии' : 'вакансий'}
          </span>
        </div>
      </div>

      {/* Empty state */}
      {results.length === 0 && !checking && (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">
          <p className="text-lg mb-2">🔍 Ничего не найдено</p>
          <p className="text-sm">Нажми «Проверить сейчас» или измени фильтры</p>
        </div>
      )}

      {/* Initial loading */}
      {results.length === 0 && checking && (
        <div className="text-center py-16 text-gray-400 dark:text-gray-500">
          <p className="text-lg mb-2">⏳ Поиск вакансий...</p>
          <p className="text-sm">Подожди, вакансии скоро появятся</p>
        </div>
      )}

      {/* Results grid */}
      {results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {results.map((v, idx) => (
            <div
              key={`${v.source}-${v.url}-${idx}`}
              className="animate-fade-in"
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              <VacancyCard vacancy={v} config={config} />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

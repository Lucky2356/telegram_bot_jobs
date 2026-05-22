import type { VacancyResult, AppConfig } from '../types'
import VacancyCard from './VacancyCard'

interface ResultsPanelProps {
  results: VacancyResult[]
  config: AppConfig
  checkedAt: string | null
  loading: boolean
}

export default function ResultsPanel({ results, config, checkedAt, loading }: ResultsPanelProps) {
  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            📋 Результаты проверки
          </h2>
          {checkedAt && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
              Последняя проверка: {new Date(checkedAt).toLocaleString('ru-RU', {
                day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
              })}
            </p>
          )}
        </div>
        <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded-full">
          {results.length} {results.length === 1 ? 'вакансия' : results.length < 5 ? 'вакансии' : 'вакансий'}
        </span>
      </div>

      {loading && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-lg mb-1">⏳ Загрузка...</p>
          <p className="text-sm">Проверка ещё выполняется</p>
        </div>
      )}

      {!loading && results.length === 0 && (
        <div className="text-center py-12 text-gray-500 dark:text-gray-400">
          <p className="text-lg mb-2">🔍 Новых вакансий пока нет</p>
          <p className="text-sm">
            Нажми «🔍 Проверить сейчас» или дождись автоматической проверки
          </p>
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-3">
          {results.map((v, idx) => (
            <VacancyCard key={`${v.source}-${v.url}-${idx}`} vacancy={v} config={config} />
          ))}
        </div>
      )}
    </div>
  )
}

import { useState, useMemo } from 'react'
import type { HistoryItem, AppConfig } from '../types'

interface HistoryPanelProps {
  history: HistoryItem[]
  config: AppConfig
}

export default function HistoryPanel({ history, config }: HistoryPanelProps) {
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')

  const sources = useMemo(() => {
    const set = new Set(history.map((h) => h.source))
    return Array.from(set).sort()
  }, [history])

  const filtered = useMemo(() => {
    return history.filter((h) => {
      if (sourceFilter && h.source !== sourceFilter) return false
      if (search) {
        const q = search.toLowerCase()
        return (
          h.vacancy_title.toLowerCase().includes(q) ||
          (h.company?.toLowerCase().includes(q) ?? false) ||
          (h.filter_name?.toLowerCase().includes(q) ?? false)
        )
      }
      return true
    })
  }, [history, search, sourceFilter])

  if (history.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500 dark:text-gray-400">
        <p className="text-lg mb-2">История пуста</p>
        <p className="text-sm">Вакансии будут появляться после проверки</p>
      </div>
    )
  }

  return (
    <>
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск по вакансии, компании или фильтру..."
          className="flex-1 min-w-[200px] px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Поиск в истории"
        />
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Фильтр по сайту"
        >
          <option value="">Все сайты</option>
          {sources.map((s) => (
            <option key={s} value={s}>
              {config.sites[s] || s}
            </option>
          ))}
        </select>
      </div>

      <p className="text-xs text-gray-400 mb-3">
        Показано {filtered.length} из {history.length}
      </p>

      <div className="overflow-x-auto">
        <table className="w-full text-sm" role="table" aria-label="История отправленных вакансий">
          <thead>
            <tr className="border-b border-gray-200 dark:border-gray-700 text-gray-500 dark:text-gray-400 text-xs uppercase">
              <th className="text-left py-3 px-2 font-medium">Вакансия</th>
              <th className="text-left py-3 px-2 font-medium hidden sm:table-cell">Компания</th>
              <th className="text-left py-3 px-2 font-medium hidden md:table-cell">Зарплата</th>
              <th className="text-left py-3 px-2 font-medium">Сайт</th>
              <th className="text-left py-3 px-2 font-medium hidden lg:table-cell">Фильтр</th>
              <th className="text-right py-3 px-2 font-medium hidden sm:table-cell">Отправлено</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((h, idx) => (
              <tr
                key={`${h.sent_at}-${idx}`}
                className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <td className="py-3 px-2">
                  <a
                    href={h.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary hover:underline font-medium"
                    aria-label={`Открыть вакансию ${h.vacancy_title}`}
                  >
                    {h.vacancy_title.length > 60
                      ? `${h.vacancy_title.slice(0, 60)}...`
                      : h.vacancy_title}
                  </a>
                </td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400 hidden sm:table-cell">
                  {h.company || '—'}
                </td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400 hidden md:table-cell">
                  {h.salary || '—'}
                </td>
                <td className="py-3 px-2">
                  <span className="px-2 py-0.5 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400">
                    {config.sites[h.source] || h.source}
                  </span>
                </td>
                <td className="py-3 px-2 text-gray-600 dark:text-gray-400 hidden lg:table-cell">
                  {h.filter_name || '—'}
                </td>
                <td className="py-3 px-2 text-right text-gray-500 dark:text-gray-500 text-xs hidden sm:table-cell whitespace-nowrap">
                  {new Date(h.sent_at).toLocaleString('ru-RU', {
                    day: 'numeric',
                    month: 'short',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}

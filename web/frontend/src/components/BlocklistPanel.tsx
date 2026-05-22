import { useState } from 'react'
import type { BlocklistItem } from '../types'
import { api } from '../api'
import { toast } from './Toast'

interface BlocklistPanelProps {
  items: BlocklistItem[]
  onRefresh: () => void
}

export default function BlocklistPanel({ items, onRefresh }: BlocklistPanelProps) {
  const [pattern, setPattern] = useState('')
  const [blockType, setBlockType] = useState<'company' | 'keyword'>('company')
  const [adding, setAdding] = useState(false)

  const handleAdd = async () => {
    if (!pattern.trim()) return
    setAdding(true)
    try {
      await api.addBlocklist(pattern.trim(), blockType)
      toast.success('Добавлено в блок-лист')
      setPattern('')
      onRefresh()
    } catch {
      toast.error('Ошибка')
    } finally {
      setAdding(false)
    }
  }
  const handleDelete = async (id: number) => {
    try {
      await api.deleteBlocklist(id)
      toast.success('Удалено из блок-листа')
      onRefresh()
    } catch { toast.error('Ошибка') }
  }

  const companies = items.filter((b) => b.type === 'company')
  const keywords = items.filter((b) => b.type === 'keyword')

  return (
    <div className="space-y-3">
      {/* Add form */}
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          placeholder="Компания или ключевое слово..."
          className="flex-1 min-w-0 px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Новый паттерн блокировки"
        />
        <select
          value={blockType}
          onChange={(e) => setBlockType(e.target.value as 'company' | 'keyword')}
          className="px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary"
          aria-label="Тип блокировки"
        >
          <option value="company">🏢 Компания</option>
          <option value="keyword">🔑 Ключевое слово</option>
        </select>
        <button
          onClick={handleAdd}
          disabled={adding || !pattern.trim()}
          className="px-4 py-2 text-sm font-medium bg-primary text-white rounded-lg hover:bg-primary-hover disabled:opacity-50 transition-all cursor-pointer whitespace-nowrap"
        >
          {adding ? '⏳' : '➕'}
        </button>
      </div>

      {items.length === 0 && (
        <div className="text-center py-6 text-gray-400">
          <p className="text-sm">🚫 Нет записей в блок-листе</p>
        </div>
      )}

      {companies.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            🏢 Компании · {companies.length}
          </h3>
          <div className="flex flex-wrap gap-2">
            {companies.map((b) => (
              <div key={b.id} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
                <span>{b.pattern}</span>
                <button
                  onClick={() => handleDelete(b.id)}
                  className="ml-0.5 hover:text-red-800 dark:hover:text-red-200 cursor-pointer"
                  aria-label={`Удалить ${b.pattern}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {keywords.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">
            🔑 Ключевые слова · {keywords.length}
          </h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((b) => (
              <div key={b.id} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 dark:bg-amber-900/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                <span>{b.pattern}</span>
                <button
                  onClick={() => handleDelete(b.id)}
                  className="ml-0.5 hover:text-amber-800 dark:hover:text-amber-200 cursor-pointer"
                  aria-label={`Удалить ${b.pattern}`}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

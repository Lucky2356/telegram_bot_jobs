import { useState } from 'react'
import type { BlocklistItem } from '../types'
import { api } from '../api'
import { toast } from './Toast'
import { X, Plus } from 'lucide-react'

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
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          placeholder="Компания или ключевое слово..."
          className="flex-1 min-w-0 h-9 px-3 text-sm border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
          aria-label="Новый паттерн блокировки"
        />
        <select
          value={blockType}
          onChange={(e) => setBlockType(e.target.value as 'company' | 'keyword')}
          className="h-9 px-3 text-sm border border-slate-300 dark:border-slate-700 rounded-lg bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-colors"
          aria-label="Тип блокировки"
        >
          <option value="company">🏢 Компания</option>
          <option value="keyword">🔑 Ключевое слово</option>
        </select>
        <button
          onClick={handleAdd}
          disabled={adding || !pattern.trim()}
          className="flex items-center gap-1 h-9 px-4 text-sm font-medium bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer whitespace-nowrap"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
      </div>

      {items.length === 0 && (
        <div className="text-center py-6 text-slate-400">
          <p className="text-sm">🚫 Нет записей в блок-листе</p>
        </div>
      )}

      {companies.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            🏢 Компании · {companies.length}
          </h3>
          <div className="flex flex-wrap gap-2">
            {companies.map((b) => (
              <div key={b.id} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-red-50 dark:bg-red-900/10 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800">
                <span>{b.pattern}</span>
                <button
                  onClick={() => handleDelete(b.id)}
                  className="ml-0.5 hover:text-red-800 dark:hover:text-red-200 cursor-pointer transition-colors"
                  aria-label={`Удалить ${b.pattern}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {keywords.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2">
            🔑 Ключевые слова · {keywords.length}
          </h3>
          <div className="flex flex-wrap gap-2">
            {keywords.map((b) => (
              <div key={b.id} className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg bg-amber-50 dark:bg-amber-900/10 text-amber-600 dark:text-amber-400 border border-amber-200 dark:border-amber-800">
                <span>{b.pattern}</span>
                <button
                  onClick={() => handleDelete(b.id)}
                  className="ml-0.5 hover:text-amber-800 dark:hover:text-amber-200 cursor-pointer transition-colors"
                  aria-label={`Удалить ${b.pattern}`}
                >
                  <X className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

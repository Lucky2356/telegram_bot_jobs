import { useState } from 'react'
import { Plus, X } from 'lucide-react'
import type { BlocklistItem } from '../types'
import { api } from '../api'
import { toast } from './toastBus'

interface BlocklistPanelProps {
  items: BlocklistItem[]
  onRefresh: () => void
}

export default function BlocklistPanel({ items, onRefresh }: BlocklistPanelProps) {
  const [pattern, setPattern] = useState('')
  const [blockType, setBlockType] = useState<'company' | 'keyword'>('company')
  const [adding, setAdding] = useState(false)

  const handleAdd = async () => {
    const clean = pattern.trim()
    if (!clean) return
    setAdding(true)
    try {
      await api.addBlocklist(clean, blockType)
      toast.success('Запись добавлена в блок-лист')
      setPattern('')
      onRefresh()
    } catch {
      toast.error('Не удалось добавить запись')
    } finally {
      setAdding(false)
    }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deleteBlocklist(id)
      toast.success('Запись удалена')
      onRefresh()
    } catch {
      toast.error('Не удалось удалить запись')
    }
  }

  const companies = items.filter((b) => b.type === 'company')
  const keywords = items.filter((b) => b.type === 'keyword')

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <input
          type="text"
          value={pattern}
          onChange={(e) => setPattern(e.target.value)}
          placeholder="Компания или слово"
          className="focus-ring h-10 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary placeholder:text-muted"
          aria-label="Новое правило блок-листа"
        />

        <div className="grid grid-cols-2 gap-2">
          <select
            value={blockType}
            onChange={(e) => setBlockType(e.target.value as 'company' | 'keyword')}
            className="focus-ring h-10 rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 text-sm text-primary"
            aria-label="Тип правила"
          >
            <option value="company">Компания</option>
            <option value="keyword">Ключевое слово</option>
          </select>
          <button
            onClick={handleAdd}
            disabled={adding || !pattern.trim()}
            className="focus-ring inline-flex h-10 items-center justify-center gap-1 rounded-xl bg-[var(--accent)] px-3 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-60"
          >
            <Plus className="h-4 w-4" />
            Добавить
          </button>
        </div>
      </div>

      {items.length === 0 && (
        <div className="rounded-xl border border-dashed border-[var(--border)] bg-[color:var(--surface-elevated)] p-6 text-center">
          <p className="text-sm text-secondary">Блок-лист пуст</p>
        </div>
      )}

      {companies.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted">Компании</h3>
          <div className="flex flex-wrap gap-1.5">
            {companies.map((item) => (
              <span key={item.id} className="inline-flex items-center gap-1 rounded-lg border border-rose-400/30 bg-rose-500/10 px-2.5 py-1 text-xs font-medium text-rose-300">
                {item.pattern}
                <button
                  onClick={() => handleDelete(item.id)}
                  className="focus-ring rounded p-0.5 text-rose-300 transition hover:bg-rose-500/20"
                  aria-label={`Удалить ${item.pattern}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </section>
      )}

      {keywords.length > 0 && (
        <section>
          <h3 className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-muted">Ключевые слова</h3>
          <div className="flex flex-wrap gap-1.5">
            {keywords.map((item) => (
              <span key={item.id} className="inline-flex items-center gap-1 rounded-lg border border-amber-400/30 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-300">
                {item.pattern}
                <button
                  onClick={() => handleDelete(item.id)}
                  className="focus-ring rounded p-0.5 text-amber-300 transition hover:bg-amber-500/20"
                  aria-label={`Удалить ${item.pattern}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}

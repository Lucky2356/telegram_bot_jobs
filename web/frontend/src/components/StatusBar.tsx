import type { ParserStatus } from '../types'

interface StatusBarProps {
  status: ParserStatus | null
  compact?: boolean
}

const labels: Record<string, string> = {
  hh: 'hh.ru',
  superjob: 'SuperJob',
  trudvsem: 'Работа России',
  rabota: 'rabota.ru',
  habr: 'Хабр Карьера',
}

export default function StatusBar({ status, compact = false }: StatusBarProps) {
  if (!status) {
    return <p className="text-xs text-muted">Статусы источников загружаются...</p>
  }

  return (
    <div className={compact ? 'grid grid-cols-1 gap-1.5' : 'flex flex-wrap items-center gap-2'}>
      {Object.entries(status).map(([key, ok]) => (
        <span
          key={key}
          className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[11px] font-medium ${
            ok
              ? 'border-emerald-400/30 bg-emerald-500/10 text-emerald-400'
              : 'border-[var(--border)] bg-[color:var(--surface-elevated)] text-muted'
          }`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${ok ? 'bg-emerald-400' : 'bg-slate-500'}`} />
          {labels[key] || key}
        </span>
      ))}
    </div>
  )
}

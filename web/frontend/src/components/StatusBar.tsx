import type { ParserStatus } from '../types'

interface StatusBarProps {
  status: ParserStatus | null
}

const labels: Record<string, string> = {
  hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России',
  rabota: 'rabota.ru', habr: 'Хабр Карьера',
}

export default function StatusBar({ status }: StatusBarProps) {
  if (!status) return null

  return (
    <div className="flex items-center gap-2 flex-wrap">
      {Object.entries(status).map(([key, ok]) => (
        <span key={key} className="flex items-center gap-1 text-[10px] text-slate-400 dark:text-slate-500">
          <span className={`w-1.5 h-1.5 rounded-full ${ok ? 'bg-emerald-500' : 'bg-slate-300 dark:bg-slate-600'}`} />
          {labels[key] || key}
        </span>
      ))}
    </div>
  )
}

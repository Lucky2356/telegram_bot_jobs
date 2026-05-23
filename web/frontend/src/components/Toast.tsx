import { useState, useCallback, useEffect, type ReactNode } from 'react'
import { X, CheckCircle2, AlertCircle, Info } from 'lucide-react'
import { setToastHandler } from './toastBus'

interface ToastData {
  message: string
  type: 'success' | 'error' | 'info'
  id: number
}

let toastId = 0

const iconMap: Record<string, ReactNode> = {
  success: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  error: <AlertCircle className="h-4 w-4 text-rose-400" />,
  info: <Info className="h-4 w-4 text-[var(--accent)]" />,
}

export default function Toast() {
  const [items, setItems] = useState<ToastData[]>([])

  const removeToast = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((data: Omit<ToastData, 'id'>) => {
    const id = ++toastId
    setItems((prev) => [...prev, { ...data, id }])
    setTimeout(() => removeToast(id), 3600)
  }, [removeToast])

  useEffect(() => {
    setToastHandler(addToast)
    return () => {
      setToastHandler(null)
    }
  }, [addToast])

  if (items.length === 0) return null

  return (
    <div className="fixed bottom-22 right-3 z-50 flex max-w-[calc(100vw-24px)] flex-col gap-2 md:bottom-4 md:right-4" role="log" aria-label="Notifications">
      {items.map((item) => (
        <div
          key={item.id}
          className="animate-fade-in-up flex min-w-[280px] max-w-[420px] items-center gap-2.5 rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3.5 py-3 text-sm text-secondary shadow-[var(--shadow-md)]"
          role="alert"
        >
          {iconMap[item.type]}
          <span className="flex-1 text-primary">{item.message}</span>
          <button
            onClick={() => removeToast(item.id)}
            className="focus-ring rounded-md p-1 text-muted transition hover:bg-[color:var(--surface-elevated)] hover:text-primary"
            aria-label="Закрыть уведомление"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}


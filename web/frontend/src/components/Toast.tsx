import { useState, useCallback, useEffect } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'

interface ToastData {
  message: string
  type: 'success' | 'error' | 'info'
  id: number
}

let toastId = 0
let addToastFn: ((data: Omit<ToastData, 'id'>) => void) | null = null

export const toast = {
  success: (message: string) => addToastFn?.({ message, type: 'success' }),
  error: (message: string) => addToastFn?.({ message, type: 'error' }),
  info: (message: string) => addToastFn?.({ message, type: 'info' }),
}

const iconMap: Record<string, React.ReactNode> = {
  success: <CheckCircle className="w-4 h-4 text-emerald-500" />,
  error: <AlertCircle className="w-4 h-4 text-red-500" />,
  info: <Info className="w-4 h-4 text-blue-500" />,
}

export default function Toast() {
  const [items, setItems] = useState<ToastData[]>([])

  const removeToast = useCallback((id: number) => {
    setItems((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const addToast = useCallback((data: Omit<ToastData, 'id'>) => {
    const id = ++toastId
    setItems((prev) => [...prev, { ...data, id }])
    setTimeout(() => removeToast(id), 3500)
  }, [removeToast])

  useEffect(() => {
    addToastFn = addToast
    return () => { addToastFn = null }
  }, [addToast])

  if (items.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="log" aria-label="Notifications">
      {items.map((item) => (
        <div
          key={item.id}
          className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-lg rounded-xl px-4 py-3 text-sm text-slate-700 dark:text-slate-300 flex items-center gap-2.5 min-w-[280px] max-w-[calc(100vw-32px)]"
          role="alert"
        >
          {iconMap[item.type]}
          <span className="flex-1">{item.message}</span>
          <button
            onClick={() => removeToast(item.id)}
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors cursor-pointer"
            aria-label="Закрыть"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  )
}

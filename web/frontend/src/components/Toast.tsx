import { useState, useCallback, useEffect } from 'react'

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

const typeStyles: Record<string, string> = {
  success: 'bg-green-600',
  error: 'bg-red-600',
  info: 'bg-gray-800 dark:bg-gray-200 dark:text-gray-900',
}

export default function Toast() {
  const [items, setItems] = useState<ToastData[]>([])

  const addToast = useCallback((data: Omit<ToastData, 'id'>) => {
    const id = ++toastId
    setItems((prev) => [...prev, { ...data, id }])
    setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id))
    }, 3500)
  }, [])

  useEffect(() => {
    addToastFn = addToast
    return () => {
      addToastFn = null
    }
  }, [addToast])

  if (items.length === 0) return null

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2" role="log" aria-label="Notifications">
      {items.map((item) => (
        <div
          key={item.id}
          className={`${typeStyles[item.type]} text-white px-4 py-3 rounded-lg shadow-lg text-sm animate-slide-up`}
          role="alert"
        >
          {item.message}
        </div>
      ))}
    </div>
  )
}

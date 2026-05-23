export interface ToastPayload {
  message: string
  type: 'success' | 'error' | 'info'
}

let handler: ((payload: ToastPayload) => void) | null = null

export function setToastHandler(next: ((payload: ToastPayload) => void) | null) {
  handler = next
}

export const toast = {
  success: (message: string) => handler?.({ message, type: 'success' }),
  error: (message: string) => handler?.({ message, type: 'error' }),
  info: (message: string) => handler?.({ message, type: 'info' }),
}

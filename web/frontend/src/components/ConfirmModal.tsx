interface ConfirmModalProps {
  open: boolean
  title: string
  message: string
  confirmLabel?: string
  cancelLabel?: string
  onConfirm: () => void
  onCancel: () => void
  danger?: boolean
}

export default function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = 'Да',
  cancelLabel = 'Отмена',
  onConfirm,
  onCancel,
  danger = false,
}: ConfirmModalProps) {
  if (!open) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-slate-950/55 p-3 md:items-center md:p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
      onClick={(e) => {
        if (e.target === e.currentTarget) onCancel()
      }}
    >
      <div className="animate-soft-scale w-full max-w-md rounded-2xl border border-[var(--border)] bg-[color:var(--surface-strong)] p-5 shadow-[var(--shadow-lg)]">
        <h3 className="text-base font-semibold text-primary">{title}</h3>
        <p className="mt-2 text-sm text-secondary">{message}</p>
        <div className="mt-6 flex items-center justify-end gap-2">
          <button
            onClick={onCancel}
            className="focus-ring inline-flex h-10 items-center justify-center rounded-xl border border-[var(--border)] bg-[color:var(--surface-elevated)] px-4 text-sm font-medium text-secondary transition hover:border-[var(--border-strong)] hover:text-primary"
          >
            {cancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`focus-ring inline-flex h-10 items-center justify-center rounded-xl px-4 text-sm font-semibold text-white transition ${
              danger ? 'bg-rose-500 hover:bg-rose-600' : 'bg-[var(--accent)] hover:bg-[var(--accent-hover)]'
            }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}

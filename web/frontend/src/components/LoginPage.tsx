import { useState } from 'react'
import { Lock, Sparkles, ShieldCheck, SearchCheck } from 'lucide-react'

interface LoginPageProps {
  onLogin: (token: string) => void
}

export default function LoginPage({ onLogin }: LoginPageProps) {
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password.trim()) return
    setLoading(true)
    setError('')

    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      const data = await resp.json()
      if (data.ok && data.token) {
        onLogin(data.token)
        return
      }
      setError(data.message || 'Неверный пароль')
    } catch {
      setError('Ошибка соединения с сервером')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden px-4 py-8 md:px-6">
      <div className="mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-6xl grid-cols-1 gap-5 lg:grid-cols-12">
        <section className="bento-card animate-fade-in-up p-6 lg:col-span-7 lg:p-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--border)] bg-[color:var(--surface-elevated)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.15em] text-secondary">
            <Sparkles className="h-3.5 w-3.5" />
            Платформа подбора вакансий
          </div>

          <h1 className="mt-5 text-3xl font-extrabold leading-tight tracking-tight md:text-5xl">
            Поиск вакансий, который работает как умный радар.
          </h1>
          <p className="mt-4 max-w-2xl text-sm leading-relaxed text-secondary md:text-base">
            Сервис агрегирует вакансии с нескольких источников, отбирает релевантные варианты,
            отправляет их в Telegram и сохраняет полную историю поиска в одном месте.
          </p>

          <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <SearchCheck className="h-4 w-4 text-[var(--accent)]" />
              <p className="mt-2 text-sm font-semibold">Умные фильтры</p>
              <p className="mt-1 text-xs text-secondary">Гибкий подбор по навыкам, локации и зарплате.</p>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <ShieldCheck className="h-4 w-4 text-[var(--accent)]" />
              <p className="mt-2 text-sm font-semibold">Синхронно с Telegram</p>
              <p className="mt-1 text-xs text-secondary">Сайт и бот работают как единый механизм.</p>
            </div>
            <div className="rounded-2xl border border-[var(--border)] bg-[color:var(--surface-elevated)] p-4">
              <Lock className="h-4 w-4 text-[var(--accent)]" />
              <p className="mt-2 text-sm font-semibold">Безопасный вход</p>
              <p className="mt-1 text-xs text-secondary">Доступ к панели только по секретному паролю.</p>
            </div>
          </div>
        </section>

        <section className="bento-card animate-soft-scale p-6 lg:col-span-5 lg:p-8">
          <h2 className="text-lg font-semibold tracking-tight">Вход в дашборд</h2>
          <p className="mt-1 text-sm text-secondary">Введите пароль администратора для продолжения.</p>

          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            <label className="block text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              Пароль
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Введите пароль"
              autoFocus
              className="focus-ring h-11 w-full rounded-xl border border-[var(--border)] bg-[color:var(--surface-strong)] px-3.5 text-sm text-primary placeholder:text-muted"
              aria-label="Пароль"
            />

            {error && (
              <p className="rounded-xl border border-rose-400/30 bg-rose-500/10 px-3 py-2 text-sm text-rose-300">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !password.trim()}
              className="focus-ring inline-flex h-11 w-full items-center justify-center rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)] disabled:cursor-not-allowed disabled:opacity-55"
            >
              {loading ? 'Проверяем доступ...' : 'Войти'}
            </button>
          </form>
        </section>
      </div>
    </div>
  )
}

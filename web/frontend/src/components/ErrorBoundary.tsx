import { Component, type ReactNode } from 'react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export default class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  handleRetry = () => {
    this.setState({ hasError: false })
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="bento-card p-8 text-center">
          <p className="text-lg font-semibold text-primary">Что-то пошло не так</p>
          <p className="mt-2 text-sm text-secondary">Интерфейс перезагрузится после повторной попытки.</p>
          <button
            onClick={this.handleRetry}
            className="focus-ring mt-4 inline-flex h-10 items-center justify-center rounded-xl bg-[var(--accent)] px-4 text-sm font-semibold text-white transition hover:bg-[var(--accent-hover)]"
          >
            Повторить
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

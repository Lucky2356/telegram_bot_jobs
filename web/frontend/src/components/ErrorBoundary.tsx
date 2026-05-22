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
        <div className="text-center py-16 text-slate-400">
          <p className="text-base mb-2">⚠️ Что-то пошло не так</p>
          <button
            onClick={this.handleRetry}
            className="px-4 py-2 text-sm font-medium text-primary border border-primary/30 rounded-xl hover:bg-primary hover:text-white transition-all cursor-pointer"
          >
            🔄 Попробовать снова
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

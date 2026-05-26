import type { ReactNode } from 'react'
import { Search, History, Bookmark, BarChart3, SlidersHorizontal } from 'lucide-react'

type TabItem = {
  key: string
  label: string
  shortLabel?: string
  icon?: string
}

interface TabsProps {
  tabs: TabItem[]
  active: string
  onTabChange: (key: string) => void
  variant?: 'sidebar' | 'bottom'
}

const iconMap: Record<string, ReactNode> = {
  search: <Search className="h-4 w-4" />,
  history: <History className="h-4 w-4" />,
  saved: <Bookmark className="h-4 w-4" />,
  stats: <BarChart3 className="h-4 w-4" />,
  control: <SlidersHorizontal className="h-4 w-4" />,
}

export default function Tabs({ tabs, active, onTabChange, variant = 'sidebar' }: TabsProps) {
  const isSidebar = variant === 'sidebar'

  return (
    <nav
      role="tablist"
      aria-orientation={isSidebar ? 'vertical' : 'horizontal'}
      className={isSidebar ? 'flex flex-col gap-1' : 'grid grid-cols-5 gap-1'}
    >
      {tabs.map((tab) => {
        const isActive = active === tab.key

        return (
          <button
            key={tab.key}
            role="tab"
            aria-selected={isActive}
            onClick={() => onTabChange(tab.key)}
            className={isSidebar
              ? `focus-ring flex h-11 items-center gap-3 rounded-xl px-3 text-sm font-medium transition ${
                  isActive
                    ? 'bg-[var(--accent-soft)] text-primary border border-[var(--border-strong)]'
                    : 'text-secondary hover:bg-[color:var(--surface-elevated)] hover:text-primary border border-transparent'
                }`
              : `focus-ring flex min-w-0 flex-col items-center justify-center gap-1 rounded-xl px-1 py-2 text-[11px] font-medium transition ${
                  isActive
                    ? 'bg-[var(--accent-soft)] text-primary border border-[var(--border-strong)]'
                    : 'text-secondary hover:bg-[color:var(--surface-elevated)] hover:text-primary border border-transparent'
                }`
            }
          >
            {iconMap[tab.icon || tab.key] || null}
            <span className={isSidebar ? 'truncate' : 'max-w-full truncate'}>{isSidebar ? tab.label : (tab.shortLabel || tab.label)}</span>
          </button>
        )
      })}
    </nav>
  )
}


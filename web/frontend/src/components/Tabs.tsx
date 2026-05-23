import { Search, History, Bookmark, BarChart3 } from 'lucide-react'

const iconMap: Record<string, React.ReactNode> = {
  search: <Search className="w-4 h-4" />,
  history: <History className="w-4 h-4" />,
  saved: <Bookmark className="w-4 h-4" />,
  stats: <BarChart3 className="w-4 h-4" />,
}

interface TabsProps {
  tabs: { key: string; label: string }[]
  active: string
  onTabChange: (key: string) => void
}

export default function Tabs({ tabs, active, onTabChange }: TabsProps) {
  const handleKeyDown = (key: string) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onTabChange(key) }
  }

  return (
    <>
      {/* Desktop sidebar */}
      <nav className="hidden md:flex flex-col gap-1 w-56 shrink-0" role="tablist">
        {tabs.map((tab) => {
          const isActive = active === tab.key
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              tabIndex={0}
              onClick={() => onTabChange(tab.key)}
              onKeyDown={handleKeyDown(tab.key)}
              className={`flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-lg transition-all cursor-pointer ${
                isActive
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950 shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-slate-700 dark:hover:text-slate-300'
              }`}
            >
              {iconMap[tab.key] || null}
              <span>{tab.label}</span>
            </button>
          )
        })}
      </nav>

      {/* Mobile horizontal tabs */}
      <div className="flex md:hidden gap-1 overflow-x-auto pb-1" role="tablist">
        {tabs.map((tab) => {
          const isActive = active === tab.key
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              tabIndex={0}
              onClick={() => onTabChange(tab.key)}
              onKeyDown={handleKeyDown(tab.key)}
              className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg whitespace-nowrap transition-all cursor-pointer ${
                isActive
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-950'
                  : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              {iconMap[tab.key] || null}
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>
    </>
  )
}

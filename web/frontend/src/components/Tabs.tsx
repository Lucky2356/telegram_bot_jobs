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
    <div className="flex gap-6 border-b border-slate-200 dark:border-slate-700/50 mb-5" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={active === tab.key}
          aria-label={tab.label}
          tabIndex={0}
          onClick={() => onTabChange(tab.key)}
          onKeyDown={handleKeyDown(tab.key)}
          className={`pb-2.5 text-sm font-medium border-b-2 transition-all cursor-pointer ${
            active === tab.key
              ? 'border-primary text-primary dark:border-primary dark:text-primary'
              : 'border-transparent text-slate-400 dark:text-slate-500 hover:text-slate-600 dark:hover:text-slate-300 hover:border-slate-300 dark:hover:border-slate-600'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

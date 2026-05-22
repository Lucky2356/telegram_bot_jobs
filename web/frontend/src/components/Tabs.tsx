interface TabsProps {
  tabs: { key: string; label: string }[]
  active: string
  onTabChange: (key: string) => void
}

export default function Tabs({ tabs, active, onTabChange }: TabsProps) {
  const handleKeyDown = (key: string) => (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      onTabChange(key)
    }
  }

  return (
    <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 mb-6" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={active === tab.key}
          aria-label={tab.label}
          tabIndex={0}
          onClick={() => onTabChange(tab.key)}
          onKeyDown={handleKeyDown(tab.key)}
          className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
            active === tab.key
              ? 'border-primary text-primary dark:border-primary dark:text-primary'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

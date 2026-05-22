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
    <div className="flex gap-1 mb-6" role="tablist">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          role="tab"
          aria-selected={active === tab.key}
          aria-label={tab.label}
          tabIndex={0}
          onClick={() => onTabChange(tab.key)}
          onKeyDown={handleKeyDown(tab.key)}
          className={`px-5 py-2.5 text-sm font-medium rounded-xl transition-all cursor-pointer ${
            active === tab.key
              ? 'bg-primary text-white shadow-sm'
              : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  )
}

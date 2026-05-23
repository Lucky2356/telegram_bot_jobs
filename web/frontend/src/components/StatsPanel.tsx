import { useMemo } from 'react'
import type { Stats } from '../types'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { Bar, Pie } from 'react-chartjs-2'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

interface StatsPanelProps {
  stats: Stats
}

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: 'bottom' as const,
      labels: { color: '#94a3b8' },
    },
  },
}

export default function StatsPanel({ stats }: StatsPanelProps) {
  const siteData = useMemo(() => ({
    labels: Object.keys(stats.sent_by_source).map(
      (k) => ({ hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России', rabota: 'rabota.ru', habr: 'Хабр Карьера' }[k] || k),
    ),
    datasets: [
      {
        label: 'Вакансий',
        data: Object.values(stats.sent_by_source),
        backgroundColor: ['#2563eb', '#06b6d4', '#10b981', '#d97706', '#e11d48'],
      },
    ],
  }), [stats.sent_by_source])

  const dayData = useMemo(() => ({
    labels: stats.sent_by_day.map((d) => {
      const date = new Date(d.date + 'T00:00:00')
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    }),
    datasets: [
      {
        label: 'Вакансий в день',
        data: stats.sent_by_day.map((d) => d.count),
        backgroundColor: '#2563eb',
        borderRadius: 4,
      },
    ],
  }), [stats.sent_by_day])

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
        <StatCard label="Всего фильтров" value={stats.total_filters} />
        <StatCard label="Активных" value={stats.active_filters} />
        <StatCard label="В базе" value={stats.total_vacancies} />
        <StatCard label="За 7 дней" value={stats.sent_last_7d} />
        <StatCard label="За 30 дней" value={stats.sent_last_30d} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 shadow-sm border border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider">
            По дням
          </h3>
          {stats.sent_by_day.length > 0 ? (
            <Bar data={dayData} options={chartOptions} />
          ) : (
            <p className="text-center text-slate-400 py-8">Нет данных за последние 30 дней</p>
          )}
        </div>
        <div className="bg-white dark:bg-slate-900 rounded-2xl p-5 shadow-sm border border-slate-200 dark:border-slate-800">
          <h3 className="text-sm font-semibold text-slate-500 dark:text-slate-400 mb-3 uppercase tracking-wider">
            По сайтам
          </h3>
          {Object.keys(stats.sent_by_source).length > 0 ? (
            <Pie data={siteData} options={chartOptions} />
          ) : (
            <p className="text-center text-slate-400 py-8">Нет данных</p>
          )}
        </div>
      </div>

      <div className="text-center py-6">
        <p className="text-4xl font-bold text-blue-600 dark:text-blue-400">{stats.total_sent}</p>
        <p className="text-sm text-slate-400 mt-1">Всего отправлено вакансий</p>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl p-4 text-center shadow-sm border border-slate-200 dark:border-slate-800">
      <p className="text-xl font-bold text-blue-600 dark:text-blue-400">{value}</p>
      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{label}</p>
    </div>
  )
}

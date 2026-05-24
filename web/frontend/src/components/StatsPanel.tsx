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

function cssVar(name: string, fallback: string) {
  if (typeof window === 'undefined') return fallback
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}

export default function StatsPanel({ stats }: StatsPanelProps) {
  const colors = useMemo(() => ({
    accent: cssVar('--accent', '#5c73ff'),
    textSecondary: cssVar('--text-secondary', '#8c9bb5'),
    border: cssVar('--border', 'rgba(127, 146, 191, 0.22)'),
    pie: ['#5c73ff', '#4bb8d8', '#31c48d', '#f0b457', '#ef6f89'],
  }), [])

  const chartOptions = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          color: colors.textSecondary,
          usePointStyle: true,
          boxWidth: 8,
        },
      },
      tooltip: {
        backgroundColor: 'rgba(12, 18, 32, 0.9)',
        borderColor: colors.border,
        borderWidth: 1,
        titleColor: '#fff',
        bodyColor: '#d6e0f5',
      },
    },
    scales: {
      y: {
        ticks: { color: colors.textSecondary },
        grid: { color: colors.border },
      },
      x: {
        ticks: { color: colors.textSecondary },
        grid: { color: 'transparent' },
      },
    },
  }), [colors])

  const sourceData = useMemo(() => ({
    labels: Object.keys(stats.sent_by_source).map(
      (key) => ({ hh: 'hh.ru', superjob: 'SuperJob', trudvsem: 'Работа России', rabota: 'rabota.ru', habr: 'Хабр Карьера' }[key] || key),
    ),
    datasets: [
      {
        label: 'Вакансий',
        data: Object.values(stats.sent_by_source),
        backgroundColor: colors.pie,
        borderColor: 'transparent',
      },
    ],
  }), [stats.sent_by_source, colors.pie])

  const dayData = useMemo(() => ({
    labels: stats.sent_by_day.map((d) => {
      const date = new Date(`${d.date}T00:00:00`)
      return date.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    }),
    datasets: [
      {
        label: 'Вакансий в день',
        data: stats.sent_by_day.map((d) => d.count),
        backgroundColor: colors.accent,
        borderRadius: 8,
      },
    ],
  }), [stats.sent_by_day, colors.accent])

  return (
    <div className="space-y-4">
      <section className="grid grid-cols-2 gap-3 md:grid-cols-5">
        <Metric title="Всего фильтров" value={stats.total_filters} />
        <Metric title="Активные" value={stats.active_filters} />
        <Metric title="В базе" value={stats.total_vacancies} />
        <Metric title="За 7 дней" value={stats.sent_last_7d} />
        <Metric title="За 30 дней" value={stats.sent_last_30d} />
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <article className="bento-card p-4 xl:col-span-8">
          <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Поток вакансий по дням</h3>
          <div className="mt-3 h-[320px]">
            {stats.sent_by_day.length > 0 ? (
              <Bar data={dayData} options={chartOptions} />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-secondary">Нет данных за последние дни</div>
            )}
          </div>
        </article>

        <article className="bento-card p-4 xl:col-span-4">
          <h3 className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Распределение по источникам</h3>
          <div className="mt-3 h-[320px]">
            {Object.keys(stats.sent_by_source).length > 0 ? (
              <Pie data={sourceData} options={{ ...chartOptions, scales: undefined }} />
            ) : (
              <div className="flex h-full items-center justify-center text-sm text-secondary">Нет данных по источникам</div>
            )}
          </div>
        </article>
      </section>

      <section className="bento-card p-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">Всего отправлено в Telegram</p>
        <p className="mt-2 code text-4xl font-bold text-primary md:text-5xl">{stats.total_sent}</p>
      </section>
    </div>
  )
}

function Metric({ title, value }: { title: string; value: number }) {
  return (
    <article className="bento-card p-4">
      <p className="code text-2xl font-bold tracking-tight text-primary">{value}</p>
      <p className="mt-1 text-xs text-secondary">{title}</p>
    </article>
  )
}

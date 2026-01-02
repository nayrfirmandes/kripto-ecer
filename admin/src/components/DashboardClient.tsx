'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import { Sidebar } from '@/components/sidebar'

interface DashboardStats {
  totalUsers: number
  activeUsers: number
  pendingDeposits: number
  pendingWithdrawals: number
  totalDepositsAmount: number | bigint | string
  totalWithdrawalsAmount: number | bigint | string
}

export function DashboardClient({ initialStats }: { initialStats: DashboardStats }) {
  const { data: stats, isLoading } = useRealTimeData<DashboardStats>(
    '/api/dashboard/stats',
    initialStats,
    3000
  )

  const statCards = [
    { 
      title: 'Total Users', 
      value: stats.totalUsers, 
      color: 'bg-blue-500',
      loading: isLoading
    },
    { 
      title: 'Active Users', 
      value: stats.activeUsers, 
      color: 'bg-green-500',
      loading: isLoading
    },
    { 
      title: 'Pending Deposits', 
      value: stats.pendingDeposits, 
      color: 'bg-yellow-500',
      loading: isLoading
    },
    { 
      title: 'Pending Withdrawals', 
      value: stats.pendingWithdrawals, 
      color: 'bg-orange-500',
      loading: isLoading
    },
    { 
      title: 'Total Deposits', 
      value: `Rp ${Number(stats.totalDepositsAmount).toLocaleString('id-ID')}`, 
      color: 'bg-emerald-500',
      loading: isLoading,
      suppressHydration: true
    },
    { 
      title: 'Total Withdrawals', 
      value: `Rp ${Number(stats.totalWithdrawalsAmount).toLocaleString('id-ID')}`, 
      color: 'bg-red-500',
      loading: isLoading,
      suppressHydration: true
    },
  ]

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 p-8 bg-gray-100">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          {isLoading && (
            <span className="text-sm text-gray-500">
              Updating data...
            </span>
          )}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {statCards.map((stat, index) => (
            <Card key={index} className={stat.loading ? 'opacity-75' : ''}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-gray-600">
                  {stat.title}
                </CardTitle>
                <span className={`${stat.color} text-white p-2 rounded-lg text-xs`}>
                  {stat.title.charAt(0)}
                </span>
              </CardHeader>
              <CardContent>
                <div 
                  className="text-2xl font-bold" 
                  suppressHydrationWarning={stat.suppressHydration}
                >
                  {stat.value}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>
    </div>
  )
}

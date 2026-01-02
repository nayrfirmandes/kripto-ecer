"use client"

import { useEffect, useState, useCallback } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface DashboardStats {
  totalUsers: number
  activeUsers: number
  pendingDeposits: number
  pendingWithdrawals: number
  totalDepositsToday: number
  totalWithdrawalsToday: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const fetchStats = useCallback(async (isPolling = false) => {
    try {
      if (isPolling) setSyncing(true)
      const res = await fetch("/api/dashboard/stats")
      if (res.ok) {
        const data = await res.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
    } finally {
      setLoading(false)
      setSyncing(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
    const interval = setInterval(() => fetchStats(true), 5000)
    return () => clearInterval(interval)
  }, [fetchStats])

  const StatCard = ({ title, value, prefix = "", isLoading = false }: { 
    title: string
    value: number | string
    prefix?: string
    isLoading?: boolean
  }) => (
    <Card className="card-hover">
      <CardHeader className="pb-2 p-4 md:p-6 md:pb-2">
        <CardDescription className="text-xs md:text-sm">{title}</CardDescription>
        {isLoading ? (
          <Skeleton className="h-7 md:h-9 w-20 skeleton-pulse" />
        ) : (
          <CardTitle className="text-xl md:text-3xl font-bold transition-smooth">
            {prefix}{typeof value === 'number' ? value.toLocaleString('id-ID') : value}
          </CardTitle>
        )}
      </CardHeader>
    </Card>
  )

  if (loading) {
    return (
      <div className="space-y-4 md:space-y-6">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Overview of your crypto trading bot</p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
          {[...Array(6)].map((_, i) => (
            <Card key={i} className="fade-in" style={{ animationDelay: `${i * 50}ms` }}>
              <CardHeader className="pb-2 p-4 md:p-6 md:pb-2">
                <Skeleton className="h-4 w-20 mb-2 skeleton-pulse" />
                <Skeleton className="h-7 md:h-9 w-16 skeleton-pulse" />
              </CardHeader>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-sm text-muted-foreground">Overview of your crypto trading bot</p>
        </div>
        {syncing && (
          <span className="text-xs text-muted-foreground animate-pulse">Syncing...</span>
        )}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
        <div className="fade-in" style={{ animationDelay: '0ms' }}>
          <StatCard title="Total Users" value={stats?.totalUsers ?? 0} />
        </div>
        <div className="fade-in" style={{ animationDelay: '50ms' }}>
          <StatCard title="Active Users" value={stats?.activeUsers ?? 0} />
        </div>
        <div className="fade-in" style={{ animationDelay: '100ms' }}>
          <StatCard title="Pending Deposits" value={stats?.pendingDeposits ?? 0} />
        </div>
        <div className="fade-in" style={{ animationDelay: '150ms' }}>
          <StatCard title="Pending Withdrawals" value={stats?.pendingWithdrawals ?? 0} />
        </div>
        <div className="fade-in" style={{ animationDelay: '200ms' }}>
          <StatCard title="Deposits Today" value={stats?.totalDepositsToday ?? 0} prefix="Rp " />
        </div>
        <div className="fade-in" style={{ animationDelay: '250ms' }}>
          <StatCard title="Withdrawals Today" value={stats?.totalWithdrawalsToday ?? 0} prefix="Rp " />
        </div>
      </div>
    </div>
  )
}

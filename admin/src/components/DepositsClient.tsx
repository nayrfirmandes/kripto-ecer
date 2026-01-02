'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import { DepositActions } from '@/app/(admin)/deposits/actions'

interface User {
  id: string
  firstName?: string
  username?: string
  telegramId: string
}

interface Deposit {
  id: string
  status: string
  amount: number
  paymentMethod: string
  createdAt: string
  user: User
}

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  PROCESSING: 'bg-blue-100 text-blue-800 border-blue-200',
  COMPLETED: 'bg-green-100 text-green-800 border-green-200',
  FAILED: 'bg-red-100 text-red-800 border-red-200',
  CANCELLED: 'bg-gray-100 text-gray-800 border-gray-200',
}

export function DepositsClient({ initialDeposits }: { initialDeposits: Deposit[] }) {
  const { data: deposits, isLoading } = useRealTimeData<Deposit[]>(
    '/api/deposits/list',
    initialDeposits,
    3000
  )

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl md:text-2xl font-bold tracking-tight">Deposits</h1>
        {isLoading && (
          <span className="text-xs md:text-sm text-muted-foreground animate-pulse">Syncing...</span>
        )}
      </div>
      <Card className="transition-smooth">
        <CardHeader className="pb-3 md:pb-4">
          <CardTitle className="text-base md:text-lg">Recent Deposits</CardTitle>
        </CardHeader>
        <CardContent className="p-0 md:p-6 md:pt-0">
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium">User</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Amount</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Method</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {deposits.map((deposit, index) => (
                  <tr 
                    key={deposit.id} 
                    className="border-b transition-smooth hover:bg-muted/50"
                    style={{ animationDelay: `${index * 30}ms` }}
                  >
                    <td className="py-3 px-4">
                      <div className="font-medium text-sm">{deposit.user.firstName || deposit.user.username}</div>
                      <div className="text-xs text-muted-foreground" suppressHydrationWarning>ID: {deposit.user.telegramId}</div>
                    </td>
                    <td className="py-3 px-4 font-medium text-sm" suppressHydrationWarning>
                      Rp {Number(deposit.amount).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-4 text-sm">{deposit.paymentMethod}</td>
                    <td className="py-3 px-4">
                      <Badge className={`${statusColors[deposit.status]} text-xs transition-smooth`}>
                        {deposit.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground" suppressHydrationWarning>
                      {new Date(deposit.createdAt).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-4">
                      {deposit.status === 'PENDING' && (
                        <DepositActions depositId={deposit.id} />
                      )}
                    </td>
                  </tr>
                ))}
                {deposits.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground text-sm">
                      No deposits found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="md:hidden divide-y">
            {deposits.map((deposit, index) => (
              <div 
                key={deposit.id} 
                className="p-4 transition-smooth hover:bg-muted/30 fade-in"
                style={{ animationDelay: `${index * 30}ms` }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium text-sm">{deposit.user.firstName || deposit.user.username}</div>
                    <div className="text-xs text-muted-foreground" suppressHydrationWarning>ID: {deposit.user.telegramId}</div>
                  </div>
                  <Badge className={`${statusColors[deposit.status]} text-xs`}>
                    {deposit.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-semibold" suppressHydrationWarning>Rp {Number(deposit.amount).toLocaleString('id-ID')}</span>
                  <span className="text-muted-foreground text-xs">{deposit.paymentMethod}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground" suppressHydrationWarning>
                    {new Date(deposit.createdAt).toLocaleString('id-ID')}
                  </span>
                  {deposit.status === 'PENDING' && (
                    <DepositActions depositId={deposit.id} />
                  )}
                </div>
              </div>
            ))}
            {deposits.length === 0 && (
              <div className="py-8 text-center text-muted-foreground text-sm">
                No deposits found
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

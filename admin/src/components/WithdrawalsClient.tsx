'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useRealTimeData } from '@/hooks/useRealTimeData'
import { WithdrawalActions } from '@/app/(admin)/withdrawals/actions'

interface User {
  id: string
  firstName?: string
  username?: string
  telegramId: string
}

interface Withdrawal {
  id: string
  status: string
  amount: number
  bankName?: string
  accountNumber?: string
  accountName?: string
  ewalletType?: string
  ewalletNumber?: string
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

export function WithdrawalsClient({ initialWithdrawals }: { initialWithdrawals: Withdrawal[] }) {
  const { data: withdrawals, isLoading } = useRealTimeData<Withdrawal[]>(
    '/api/withdrawals/list',
    initialWithdrawals,
    3000
  )

  const getDestination = (withdrawal: Withdrawal) => {
    if (withdrawal.bankName) {
      return { type: withdrawal.bankName, detail: withdrawal.accountNumber }
    }
    return { type: withdrawal.ewalletType, detail: withdrawal.ewalletNumber }
  }

  return (
    <div className="space-y-4 md:space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl md:text-2xl font-bold tracking-tight">Withdrawals</h1>
        {isLoading && (
          <span className="text-xs md:text-sm text-muted-foreground animate-pulse">Syncing...</span>
        )}
      </div>
      <Card className="transition-smooth">
        <CardHeader className="pb-3 md:pb-4">
          <CardTitle className="text-base md:text-lg">Recent Withdrawals</CardTitle>
        </CardHeader>
        <CardContent className="p-0 md:p-6 md:pt-0">
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium">User</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Amount</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Destination</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {withdrawals.map((withdrawal, index) => (
                  <tr 
                    key={withdrawal.id} 
                    className="border-b transition-smooth hover:bg-muted/50"
                    style={{ animationDelay: `${index * 30}ms` }}
                  >
                    <td className="py-3 px-4">
                      <div className="font-medium text-sm">{withdrawal.user.firstName || withdrawal.user.username}</div>
                      <div className="text-xs text-muted-foreground" suppressHydrationWarning>ID: {withdrawal.user.telegramId}</div>
                    </td>
                    <td className="py-3 px-4 font-medium text-sm" suppressHydrationWarning>
                      Rp {Number(withdrawal.amount).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-4">
                      {withdrawal.bankName ? (
                        <div>
                          <div className="font-medium text-sm">{withdrawal.bankName}</div>
                          <div className="text-xs text-muted-foreground" suppressHydrationWarning>{withdrawal.accountNumber}</div>
                        </div>
                      ) : (
                        <div>
                          <div className="font-medium text-sm">{withdrawal.ewalletType}</div>
                          <div className="text-xs text-muted-foreground" suppressHydrationWarning>{withdrawal.ewalletNumber}</div>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <Badge className={`${statusColors[withdrawal.status]} text-xs transition-smooth`}>
                        {withdrawal.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground" suppressHydrationWarning>
                      {new Date(withdrawal.createdAt).toLocaleString('id-ID')}
                    </td>
                    <td className="py-3 px-4">
                      {withdrawal.status === 'PENDING' && (
                        <WithdrawalActions withdrawalId={withdrawal.id} />
                      )}
                    </td>
                  </tr>
                ))}
                {withdrawals.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground text-sm">
                      No withdrawals found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="md:hidden divide-y">
            {withdrawals.map((withdrawal, index) => {
              const dest = getDestination(withdrawal)
              return (
                <div 
                  key={withdrawal.id} 
                  className="p-4 transition-smooth hover:bg-muted/30 fade-in"
                  style={{ animationDelay: `${index * 30}ms` }}
                >
                  <div className="flex items-start justify-between mb-2">
                    <div>
                      <div className="font-medium text-sm">{withdrawal.user.firstName || withdrawal.user.username}</div>
                      <div className="text-xs text-muted-foreground" suppressHydrationWarning>ID: {withdrawal.user.telegramId}</div>
                    </div>
                    <Badge className={`${statusColors[withdrawal.status]} text-xs`}>
                      {withdrawal.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-sm mb-2">
                    <span className="font-semibold" suppressHydrationWarning>Rp {Number(withdrawal.amount).toLocaleString('id-ID')}</span>
                    <div className="text-right">
                      <div className="text-xs font-medium">{dest.type}</div>
                      <div className="text-xs text-muted-foreground" suppressHydrationWarning>{dest.detail}</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-muted-foreground" suppressHydrationWarning>
                      {new Date(withdrawal.createdAt).toLocaleString('id-ID')}
                    </span>
                    {withdrawal.status === 'PENDING' && (
                      <WithdrawalActions withdrawalId={withdrawal.id} />
                    )}
                  </div>
                </div>
              )
            })}
            {withdrawals.length === 0 && (
              <div className="py-8 text-center text-muted-foreground text-sm">
                No withdrawals found
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

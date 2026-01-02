import { prisma } from '@/lib/prisma'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

async function getUsers() {
  return prisma.user.findMany({
    include: { balance: true },
    orderBy: { createdAt: 'desc' },
    take: 100,
  })
}

const statusColors: Record<string, string> = {
  PENDING: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  ACTIVE: 'bg-green-100 text-green-800 border-green-200',
  INACTIVE: 'bg-gray-100 text-gray-800 border-gray-200',
  BANNED: 'bg-red-100 text-red-800 border-red-200',
}

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0]
}

function formatCurrency(amount: number): string {
  return `Rp ${amount.toLocaleString('id-ID')}`
}

export default async function UsersPage() {
  const users = await getUsers()

  return (
    <div className="space-y-4 md:space-y-6">
      <h1 className="text-xl md:text-2xl font-bold tracking-tight">Users</h1>
      <Card className="transition-smooth">
        <CardHeader className="pb-3 md:pb-4">
          <CardTitle className="text-base md:text-lg">All Users ({users.length})</CardTitle>
        </CardHeader>
        <CardContent className="p-0 md:p-6 md:pt-0">
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium">User</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Contact</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Balance</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Referral Code</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium">Joined</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className="border-b transition-smooth hover:bg-muted/50">
                    <td className="py-3 px-4">
                      <div className="font-medium text-sm">{user.firstName} {user.lastName}</div>
                      <div className="text-xs text-muted-foreground">@{user.username || 'N/A'}</div>
                      <div className="text-xs text-muted-foreground">ID: {user.telegramId.toString()}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-sm">{user.email || '-'}</div>
                      <div className="text-xs text-muted-foreground">{user.whatsapp || '-'}</div>
                    </td>
                    <td className="py-3 px-4 font-medium text-sm">
                      {formatCurrency(Number(user.balance?.amount || 0))}
                    </td>
                    <td className="py-3 px-4">
                      <code className="bg-muted px-2 py-1 rounded text-xs">
                        {user.referralCode}
                      </code>
                    </td>
                    <td className="py-3 px-4">
                      <Badge className={`${statusColors[user.status]} text-xs`}>
                        {user.status}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-xs text-muted-foreground">
                      {formatDate(user.createdAt)}
                    </td>
                  </tr>
                ))}
                {users.length === 0 && (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-foreground text-sm">
                      No users found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="md:hidden divide-y">
            {users.map((user) => (
              <div key={user.id} className="p-4 transition-smooth hover:bg-muted/30">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-medium text-sm">{user.firstName} {user.lastName}</div>
                    <div className="text-xs text-muted-foreground">@{user.username || 'N/A'}</div>
                  </div>
                  <Badge className={`${statusColors[user.status]} text-xs`}>
                    {user.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-semibold">{formatCurrency(Number(user.balance?.amount || 0))}</span>
                  <code className="bg-muted px-2 py-0.5 rounded text-xs">{user.referralCode}</code>
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{user.email || user.whatsapp || 'No contact'}</span>
                  <span>{formatDate(user.createdAt)}</span>
                </div>
              </div>
            ))}
            {users.length === 0 && (
              <div className="py-8 text-center text-muted-foreground text-sm">
                No users found
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

import { prisma } from '@/lib/prisma'
import { WithdrawalsClient } from '@/components/WithdrawalsClient'

async function getWithdrawals() {
  const withdrawals = await prisma.withdrawal.findMany({
    include: { user: true },
    orderBy: { createdAt: 'desc' },
    take: 50,
  })

  return withdrawals.map(w => ({
    ...w,
    amount: Number(w.amount),
    user: {
      ...w.user,
      telegramId: w.user.telegramId.toString(),
    },
  }))
}

export default async function WithdrawalsPage() {
  const initialWithdrawals = await getWithdrawals()

  return <WithdrawalsClient initialWithdrawals={initialWithdrawals as any} />
}

import { prisma } from '@/lib/prisma'
import { DepositsClient } from '@/components/DepositsClient'

async function getDeposits() {
  const deposits = await prisma.deposit.findMany({
    include: { user: true },
    orderBy: { createdAt: 'desc' },
    take: 50,
  })

  return deposits.map(d => ({
    ...d,
    amount: Number(d.amount),
    user: {
      ...d.user,
      telegramId: d.user.telegramId.toString(),
    },
  }))
}

export default async function DepositsPage() {
  const initialDeposits = await getDeposits()

  return <DepositsClient initialDeposits={initialDeposits as any} />
}

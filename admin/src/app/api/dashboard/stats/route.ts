import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const [
      totalUsers,
      activeUsers,
      pendingDeposits,
      pendingWithdrawals,
      totalDeposits,
      totalWithdrawals,
    ] = await Promise.all([
      prisma.user.count(),
      prisma.user.count({ where: { status: 'ACTIVE' } }),
      prisma.deposit.count({ where: { status: 'PENDING' } }),
      prisma.withdrawal.count({ where: { status: 'PENDING' } }),
      prisma.deposit.aggregate({
        where: { status: 'COMPLETED' },
        _sum: { amount: true },
      }),
      prisma.withdrawal.aggregate({
        where: { status: 'COMPLETED' },
        _sum: { amount: true },
      }),
    ])

    return NextResponse.json({
      totalUsers,
      activeUsers,
      pendingDeposits,
      pendingWithdrawals,
      totalDepositsAmount: totalDeposits._sum.amount ? Number(totalDeposits._sum.amount) : 0,
      totalWithdrawalsAmount: totalWithdrawals._sum.amount ? Number(totalWithdrawals._sum.amount) : 0,
    })
  } catch (error) {
    console.error('Dashboard stats error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch stats' },
      { status: 500 }
    )
  }
}

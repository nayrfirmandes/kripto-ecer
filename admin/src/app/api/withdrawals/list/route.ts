import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const withdrawals = await prisma.withdrawal.findMany({
      include: { user: true },
      orderBy: { createdAt: 'desc' },
      take: 50,
    })

    // Convert Decimal amounts to numbers and BigInt to string for JSON serialization
    const serialized = withdrawals.map(w => ({
      ...w,
      amount: Number(w.amount),
      user: {
        ...w.user,
        telegramId: w.user.telegramId.toString(),
      },
    }))

    return NextResponse.json(serialized)
  } catch (error) {
    console.error('Withdrawals list error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch withdrawals' },
      { status: 500 }
    )
  }
}

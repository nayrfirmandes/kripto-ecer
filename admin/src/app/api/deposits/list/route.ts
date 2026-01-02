import { prisma } from '@/lib/prisma'
import { NextResponse } from 'next/server'

export async function GET() {
  try {
    const deposits = await prisma.deposit.findMany({
      include: { user: true },
      orderBy: { createdAt: 'desc' },
      take: 50,
    })

    // Convert Decimal amounts to numbers and BigInt to string for JSON serialization
    const serialized = deposits.map(d => ({
      ...d,
      amount: Number(d.amount),
      user: {
        ...d.user,
        telegramId: d.user.telegramId.toString(),
      },
    }))

    return NextResponse.json(serialized)
  } catch (error) {
    console.error('Deposits list error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch deposits' },
      { status: 500 }
    )
  }
}

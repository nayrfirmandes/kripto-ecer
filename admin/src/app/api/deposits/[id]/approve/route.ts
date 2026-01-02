import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    const deposit = await prisma.deposit.findUnique({
      where: { id },
      include: { user: true },
    })

    if (!deposit) {
      return NextResponse.json({ error: 'Deposit not found' }, { status: 404 })
    }

    if (deposit.status !== 'PENDING') {
      return NextResponse.json({ error: 'Deposit already processed' }, { status: 400 })
    }

    // Update deposit status
    await prisma.deposit.update({
      where: { id },
      data: { status: 'COMPLETED' },
    })

    // Upsert balance (create if not exists, increment if exists)
    await prisma.balance.upsert({
      where: { userId: deposit.userId },
      create: {
        userId: deposit.userId,
        amount: deposit.amount,
      },
      update: {
        amount: { increment: deposit.amount },
      },
    })

    // Update transaction linked to this deposit
    await prisma.transaction.updateMany({
      where: { 
        userId: deposit.userId,
        type: 'TOPUP',
        status: 'PENDING',
        metadata: {
          path: ['depositId'],
          equals: id,
        },
      },
      data: { status: 'COMPLETED' },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Approve deposit error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

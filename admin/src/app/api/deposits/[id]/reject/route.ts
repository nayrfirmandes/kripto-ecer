import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { reason } = await request.json()

    const deposit = await prisma.deposit.findUnique({
      where: { id },
    })

    if (!deposit) {
      return NextResponse.json({ error: 'Deposit not found' }, { status: 404 })
    }

    if (deposit.status !== 'PENDING') {
      return NextResponse.json({ error: 'Deposit already processed' }, { status: 400 })
    }

    await prisma.$transaction([
      prisma.deposit.update({
        where: { id },
        data: { 
          status: 'CANCELLED',
          adminNote: reason,
        },
      }),
      prisma.transaction.updateMany({
        where: { 
          userId: deposit.userId,
          type: 'TOPUP',
          status: 'PENDING',
        },
        data: { status: 'CANCELLED' },
      }),
    ])

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Reject deposit error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

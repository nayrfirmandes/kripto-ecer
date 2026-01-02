import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(request: NextRequest) {
  try {
    const { type, name, accountNo, accountName } = await request.json()

    await prisma.paymentMethod.create({
      data: {
        type,
        name,
        accountNo,
        accountName,
        isActive: true,
      },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Add payment method error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

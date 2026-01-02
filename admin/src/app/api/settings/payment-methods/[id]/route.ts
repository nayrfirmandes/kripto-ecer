import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { isActive } = await request.json()

    await prisma.paymentMethod.update({
      where: { id },
      data: { isActive },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Update payment method error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    await prisma.paymentMethod.delete({
      where: { id },
    })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Delete payment method error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

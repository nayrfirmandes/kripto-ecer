import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(request: NextRequest) {
  try {
    const { referrerBonus, refereeBonus } = await request.json()

    const existing = await prisma.referralSetting.findFirst()

    if (existing) {
      await prisma.referralSetting.update({
        where: { id: existing.id },
        data: { referrerBonus, refereeBonus },
      })
    } else {
      await prisma.referralSetting.create({
        data: { referrerBonus, refereeBonus, isActive: true },
      })
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Save referral settings error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

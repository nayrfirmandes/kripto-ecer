import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

export async function POST(request: NextRequest) {
  try {
    const { settings } = await request.json()

    for (const setting of settings) {
      const existing = await prisma.coinSetting.findFirst({
        where: {
          coinSymbol: setting.symbol,
          network: setting.network,
        },
      })

      if (existing) {
        await prisma.coinSetting.update({
          where: { id: existing.id },
          data: {
            buyMargin: setting.buyMargin,
            sellMargin: setting.sellMargin,
          },
        })
      } else {
        await prisma.coinSetting.create({
          data: {
            coinSymbol: setting.symbol,
            network: setting.network,
            buyMargin: setting.buyMargin,
            sellMargin: setting.sellMargin,
            minBuy: 50000,
            maxBuy: 100000000,
            minSell: 50000,
            maxSell: 100000000,
            isActive: true,
          },
        })
      }
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Save coin settings error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

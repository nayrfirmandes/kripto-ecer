import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

async function notifyUserWithdrawalApproved(telegramId: string, amount: string) {
  try {
    const botToken = process.env.TELEGRAM_BOT_TOKEN
    if (!botToken) return

    const message = `✅ <b>Withdraw Disetujui</b>\n\nJumlah: Rp ${amount}\n\nUang akan segera ditransfer ke rekening Anda.`
    
    await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: telegramId,
        text: message,
        parse_mode: 'HTML',
      }),
    })
  } catch (error) {
    console.error('Failed to send approval notification:', error)
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params

    const withdrawal = await prisma.withdrawal.findUnique({
      where: { id },
      include: { user: true },
    })

    if (!withdrawal) {
      return NextResponse.json({ error: 'Withdrawal not found' }, { status: 404 })
    }

    if (withdrawal.status !== 'PENDING') {
      return NextResponse.json({ error: 'Withdrawal already processed' }, { status: 400 })
    }

    await prisma.$transaction([
      prisma.withdrawal.update({
        where: { id },
        data: { status: 'COMPLETED' },
      }),
      prisma.balance.update({
        where: { userId: withdrawal.userId },
        data: { amount: { decrement: withdrawal.amount } },
      }),
      prisma.transaction.updateMany({
        where: { 
          userId: withdrawal.userId,
          type: 'WITHDRAW',
          status: 'PENDING',
        },
        data: { status: 'COMPLETED' },
      }),
    ])

    // Notify user via Telegram
    if (withdrawal.user) {
      await notifyUserWithdrawalApproved(
        withdrawal.user.telegramId.toString(),
        withdrawal.amount.toLocaleString('id-ID')
      )
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Approve withdrawal error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

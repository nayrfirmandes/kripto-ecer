import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'

async function notifyUserWithdrawalRejected(telegramId: string, amount: string, reason: string) {
  try {
    const botToken = process.env.TELEGRAM_BOT_TOKEN
    if (!botToken) return

    const message = `❌ <b>Withdraw Ditolak</b>\n\nJumlah: Rp ${amount}\nAlasan: ${reason || 'Tidak ada keterangan'}\n\nSaldo telah dikembalikan ke akun Anda.`
    
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
    console.error('Failed to send rejection notification:', error)
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { reason } = await request.json()

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
        data: { 
          status: 'CANCELLED',
          adminNote: reason,
        },
      }),
      prisma.balance.update({
        where: { userId: withdrawal.userId },
        data: { amount: { increment: withdrawal.amount } },
      }),
      prisma.transaction.updateMany({
        where: { 
          userId: withdrawal.userId,
          type: 'WITHDRAW',
          status: 'PENDING',
        },
        data: { status: 'CANCELLED' },
      }),
    ])

    // Notify user via Telegram
    if (withdrawal.user) {
      await notifyUserWithdrawalRejected(
        withdrawal.user.telegramId.toString(),
        withdrawal.amount.toLocaleString('id-ID'),
        reason || ''
      )
    }

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Reject withdrawal error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

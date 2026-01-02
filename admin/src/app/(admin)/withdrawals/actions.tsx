'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export function WithdrawalActions({ withdrawalId }: { withdrawalId: string }) {
  const router = useRouter()

  const handleApprove = async () => {
    if (!confirm('Approve withdrawal ini? Pastikan sudah transfer ke rekening user.')) return

    const res = await fetch(`/api/withdrawals/${withdrawalId}/approve`, {
      method: 'POST',
    })

    if (res.ok) {
      router.refresh()
    } else {
      alert('Gagal approve withdrawal')
    }
  }

  const handleReject = async () => {
    const reason = prompt('Alasan reject:')
    if (!reason) return

    const res = await fetch(`/api/withdrawals/${withdrawalId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })

    if (res.ok) {
      router.refresh()
    } else {
      alert('Gagal reject withdrawal')
    }
  }

  return (
    <div className="flex gap-2">
      <Button size="sm" onClick={handleApprove}>
        Approve
      </Button>
      <Button size="sm" variant="destructive" onClick={handleReject}>
        Reject
      </Button>
    </div>
  )
}

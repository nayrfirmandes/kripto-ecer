'use client'

import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'

export function DepositActions({ depositId }: { depositId: string }) {
  const router = useRouter()

  const handleApprove = async () => {
    if (!confirm('Approve deposit ini?')) return

    const res = await fetch(`/api/deposits/${depositId}/approve`, {
      method: 'POST',
    })

    if (res.ok) {
      router.refresh()
    } else {
      alert('Gagal approve deposit')
    }
  }

  const handleReject = async () => {
    const reason = prompt('Alasan reject:')
    if (!reason) return

    const res = await fetch(`/api/deposits/${depositId}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reason }),
    })

    if (res.ok) {
      router.refresh()
    } else {
      alert('Gagal reject deposit')
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

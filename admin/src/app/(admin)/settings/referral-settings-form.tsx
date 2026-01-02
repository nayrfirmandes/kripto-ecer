'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface ReferralSetting {
  id: string
  referrerBonus: number
  refereeBonus: number
  isActive: boolean
}

export function ReferralSettingsForm({ setting }: { setting: ReferralSetting | null }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setStatus(null)

    const formData = new FormData(e.currentTarget)

    try {
      const res = await fetch('/api/settings/referral', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          referrerBonus: parseFloat(formData.get('referrerBonus') as string),
          refereeBonus: parseFloat(formData.get('refereeBonus') as string),
        }),
      })

      if (res.ok) {
        setStatus({ type: 'success', message: 'Pengaturan referral berhasil disimpan' })
        router.refresh()
        setTimeout(() => setStatus(null), 3000)
      } else {
        setStatus({ type: 'error', message: 'Gagal menyimpan pengaturan' })
      }
    } catch {
      setStatus({ type: 'error', message: 'Terjadi kesalahan jaringan' })
    }

    setLoading(false)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-md">
      <div>
        <Label className="text-sm">Bonus Referrer (Rp)</Label>
        <Input
          name="referrerBonus"
          type="number"
          step="0.01"
          defaultValue={setting?.referrerBonus || 10000}
          placeholder="Bonus untuk yang mengajak (Rp)"
          className="mt-1"
        />
        <p className="text-xs text-muted-foreground mt-1">Bonus yang didapat oleh user yang mengajak</p>
      </div>
      <div>
        <Label className="text-sm">Bonus Referee (Rp)</Label>
        <Input
          name="refereeBonus"
          type="number"
          step="0.01"
          defaultValue={setting?.refereeBonus || 5000}
          placeholder="Bonus untuk yang diajak (Rp)"
          className="mt-1"
        />
        <p className="text-xs text-muted-foreground mt-1">Bonus yang didapat oleh user baru yang diajak</p>
      </div>
      
      <div className="flex items-center gap-3 flex-wrap">
        <Button type="submit" disabled={loading} className="transition-smooth">
          {loading ? 'Menyimpan...' : 'Simpan Pengaturan'}
        </Button>
        
        {status && (
          <span 
            className={`text-sm px-3 py-1.5 rounded-md fade-in ${
              status.type === 'success' 
                ? 'bg-green-100 text-green-800' 
                : 'bg-red-100 text-red-800'
            }`}
          >
            {status.message}
          </span>
        )}
      </div>
    </form>
  )
}

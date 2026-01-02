'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

interface CoinSetting {
  id: string
  coinSymbol: string
  network: string
  buyMargin: number
  sellMargin: number
  isActive: boolean
}

const defaultCoins = [
  { symbol: 'BTC', networks: ['Bitcoin'] },
  { symbol: 'ETH', networks: ['Ethereum', 'BSC', 'Base'] },
  { symbol: 'BNB', networks: ['BSC'] },
  { symbol: 'SOL', networks: ['Solana'] },
  { symbol: 'USDT', networks: ['Tron', 'Ethereum', 'BSC', 'Polygon', 'Solana', 'The Open Network'] },
  { symbol: 'USDC', networks: ['Ethereum', 'BSC', 'Solana', 'Base'] },
]

export function CoinSettingsForm({ settings }: { settings: CoinSetting[] }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)
    setStatus(null)

    const formData = new FormData(e.currentTarget)
    const updates: { symbol: string; network: string; buyMargin: number; sellMargin: number }[] = []

    defaultCoins.forEach(coin => {
      coin.networks.forEach(network => {
        const key = `${coin.symbol}-${network}`
        const buyMargin = parseFloat(formData.get(`buy-${key}`) as string) || 2
        const sellMargin = parseFloat(formData.get(`sell-${key}`) as string) || 2
        updates.push({ symbol: coin.symbol, network, buyMargin, sellMargin })
      })
    })

    try {
      const res = await fetch('/api/settings/coins', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: updates }),
      })

      if (res.ok) {
        setStatus({ type: 'success', message: 'Pengaturan margin berhasil disimpan' })
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

  const getSetting = (symbol: string, network: string) => {
    return settings.find(s => s.coinSymbol === symbol && s.network === network)
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 md:space-y-6">
      {defaultCoins.map(coin => (
        <div key={coin.symbol} className="border rounded-lg p-3 md:p-4 transition-smooth">
          <h3 className="font-bold mb-3 text-sm md:text-base">{coin.symbol}</h3>
          <div className="grid gap-3 md:gap-4">
            {coin.networks.map(network => {
              const setting = getSetting(coin.symbol, network)
              const key = `${coin.symbol}-${network}`
              return (
                <div key={key} className="grid grid-cols-3 gap-2 md:gap-4 items-center">
                  <span className="text-xs md:text-sm text-muted-foreground">{network}</span>
                  <div>
                    <Label className="text-xs">Buy Margin %</Label>
                    <Input
                      name={`buy-${key}`}
                      type="number"
                      step="0.1"
                      defaultValue={setting?.buyMargin || 2}
                      className="w-full h-8 md:h-9 text-sm"
                    />
                  </div>
                  <div>
                    <Label className="text-xs">Sell Margin %</Label>
                    <Input
                      name={`sell-${key}`}
                      type="number"
                      step="0.1"
                      defaultValue={setting?.sellMargin || 2}
                      className="w-full h-8 md:h-9 text-sm"
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
      
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

'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'

interface PaymentMethod {
  id: string
  type: string
  name: string
  accountNo: string | null
  accountName: string | null
  isActive: boolean
}

export function PaymentMethodsForm({ methods }: { methods: PaymentMethod[] }) {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [status, setStatus] = useState<{ type: 'success' | 'error'; message: string } | null>(null)

  const showStatus = (type: 'success' | 'error', message: string) => {
    setStatus({ type, message })
    setTimeout(() => setStatus(null), 3000)
  }

  const handleAdd = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setLoading(true)

    const formData = new FormData(e.currentTarget)

    try {
      const res = await fetch('/api/settings/payment-methods', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: formData.get('type'),
          name: formData.get('name'),
          accountNo: formData.get('accountNo'),
          accountName: formData.get('accountName'),
        }),
      })

      if (res.ok) {
        setShowForm(false)
        showStatus('success', 'Metode pembayaran berhasil ditambahkan')
        router.refresh()
      } else {
        showStatus('error', 'Gagal menambah metode pembayaran')
      }
    } catch {
      showStatus('error', 'Terjadi kesalahan jaringan')
    }

    setLoading(false)
  }

  const handleToggle = async (id: string, isActive: boolean) => {
    try {
      const res = await fetch(`/api/settings/payment-methods/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ isActive: !isActive }),
      })

      if (res.ok) {
        showStatus('success', `Metode ${isActive ? 'dinonaktifkan' : 'diaktifkan'}`)
        router.refresh()
      } else {
        showStatus('error', 'Gagal mengubah status')
      }
    } catch {
      showStatus('error', 'Terjadi kesalahan jaringan')
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Hapus metode pembayaran ini?')) return

    try {
      const res = await fetch(`/api/settings/payment-methods/${id}`, {
        method: 'DELETE',
      })

      if (res.ok) {
        showStatus('success', 'Metode pembayaran berhasil dihapus')
        router.refresh()
      } else {
        showStatus('error', 'Gagal menghapus')
      }
    } catch {
      showStatus('error', 'Terjadi kesalahan jaringan')
    }
  }

  return (
    <div className="space-y-4">
      {status && (
        <div 
          className={`text-sm px-3 py-2 rounded-md fade-in ${
            status.type === 'success' 
              ? 'bg-green-100 text-green-800' 
              : 'bg-red-100 text-red-800'
          }`}
        >
          {status.message}
        </div>
      )}

      <div className="hidden md:block overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2 text-sm font-medium">Type</th>
              <th className="text-left py-2 text-sm font-medium">Name</th>
              <th className="text-left py-2 text-sm font-medium">Account</th>
              <th className="text-left py-2 text-sm font-medium">Status</th>
              <th className="text-left py-2 text-sm font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {methods.map(method => (
              <tr key={method.id} className="border-b transition-smooth hover:bg-muted/50">
                <td className="py-2 text-sm">{method.type}</td>
                <td className="py-2 text-sm">{method.name}</td>
                <td className="py-2">
                  <div className="text-sm" suppressHydrationWarning>{method.accountNo}</div>
                  <div className="text-xs text-muted-foreground">{method.accountName}</div>
                </td>
                <td className="py-2">
                  <Badge className={`text-xs ${method.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {method.isActive ? 'Active' : 'Inactive'}
                  </Badge>
                </td>
                <td className="py-2 space-x-2">
                  <Button size="sm" variant="outline" onClick={() => handleToggle(method.id, method.isActive)}>
                    {method.isActive ? 'Disable' : 'Enable'}
                  </Button>
                  <Button size="sm" variant="destructive" onClick={() => handleDelete(method.id)}>
                    Delete
                  </Button>
                </td>
              </tr>
            ))}
            {methods.length === 0 && (
              <tr>
                <td colSpan={5} className="py-4 text-center text-muted-foreground text-sm">
                  Belum ada metode pembayaran
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="md:hidden divide-y">
        {methods.map(method => (
          <div key={method.id} className="py-3 transition-smooth">
            <div className="flex items-start justify-between mb-2">
              <div>
                <div className="font-medium text-sm">{method.name}</div>
                <div className="text-xs text-muted-foreground">{method.type}</div>
              </div>
              <Badge className={`text-xs ${method.isActive ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                {method.isActive ? 'Active' : 'Inactive'}
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground mb-2" suppressHydrationWarning>
              {method.accountNo} - {method.accountName}
            </div>
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => handleToggle(method.id, method.isActive)}>
                {method.isActive ? 'Disable' : 'Enable'}
              </Button>
              <Button size="sm" variant="destructive" onClick={() => handleDelete(method.id)}>
                Delete
              </Button>
            </div>
          </div>
        ))}
        {methods.length === 0 && (
          <div className="py-4 text-center text-muted-foreground text-sm">
            Belum ada metode pembayaran
          </div>
        )}
      </div>

      {showForm ? (
        <form onSubmit={handleAdd} className="border rounded-lg p-4 space-y-4 fade-in">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-sm">Type</Label>
              <select name="type" className="w-full border rounded-md p-2 mt-1 text-sm" required>
                <option value="BANK">Bank</option>
                <option value="EWALLET">E-Wallet</option>
              </select>
            </div>
            <div>
              <Label className="text-sm">Name</Label>
              <Input name="name" placeholder="BCA / DANA / GoPay" required className="mt-1" />
            </div>
            <div>
              <Label className="text-sm">Account Number</Label>
              <Input name="accountNo" placeholder="1234567890" required className="mt-1" />
            </div>
            <div>
              <Label className="text-sm">Account Name</Label>
              <Input name="accountName" placeholder="PT Crypto Indonesia" required className="mt-1" />
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={loading} className="transition-smooth">
              {loading ? 'Adding...' : 'Add Method'}
            </Button>
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <Button onClick={() => setShowForm(true)} className="transition-smooth">
          Add Payment Method
        </Button>
      )}
    </div>
  )
}

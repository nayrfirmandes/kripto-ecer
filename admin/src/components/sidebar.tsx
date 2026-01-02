'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'

const menuItems = [
  { href: '/dashboard', label: 'Dashboard', icon: '📊' },
  { href: '/deposits', label: 'Deposits', icon: '💰' },
  { href: '/withdrawals', label: 'Withdrawals', icon: '💸' },
  { href: '/users', label: 'Users', icon: '👥' },
  { href: '/settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar() {
  const pathname = usePathname()
  const router = useRouter()

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' })
    router.push('/login')
  }

  return (
    <div className="w-64 bg-gray-900 text-white min-h-screen p-4">
      <div className="text-xl font-bold mb-8 text-center py-4 border-b border-gray-700">
        CryptoBot Admin
      </div>
      <nav className="space-y-2">
        {menuItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
              pathname === item.href
                ? 'bg-blue-600 text-white'
                : 'text-gray-300 hover:bg-gray-800'
            }`}
          >
            <span>{item.icon}</span>
            <span>{item.label}</span>
          </Link>
        ))}
      </nav>
      <div className="absolute bottom-4 left-4 right-4">
        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
        >
          <span>🚪</span>
          <span>Logout</span>
        </button>
      </div>
    </div>
  )
}

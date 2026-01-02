'use server'

import { cookies } from 'next/headers'
import { redirect } from 'next/navigation'
import { prisma } from '@/lib/prisma'
import { verifyPassword, generateToken } from '@/lib/auth'

export async function loginAction(formData: FormData) {
  const username = formData.get('username') as string
  const password = formData.get('password') as string

  if (!username || !password) {
    return { error: 'Username dan password wajib diisi' }
  }

  const admin = await prisma.admin.findUnique({
    where: { username },
  })

  if (!admin) {
    return { error: 'Username atau password salah' }
  }

  const isValid = await verifyPassword(password, admin.passwordHash)

  if (!isValid) {
    return { error: 'Username atau password salah' }
  }

  const token = generateToken({ id: admin.id, username: admin.username })
  
  const cookieStore = await cookies()
  cookieStore.set('admin_token', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7,
  })

  redirect('/dashboard')
}

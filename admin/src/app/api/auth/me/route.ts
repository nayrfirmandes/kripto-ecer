import { NextRequest, NextResponse } from 'next/server'
import { prisma } from '@/lib/prisma'
import { verifyToken } from '@/lib/auth'

export async function GET(request: NextRequest) {
  try {
    const token = request.cookies.get('admin_token')?.value

    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const payload = verifyToken(token)

    if (!payload) {
      return NextResponse.json({ error: 'Invalid token' }, { status: 401 })
    }

    const admin = await prisma.admin.findUnique({
      where: { id: payload.id },
      select: {
        id: true,
        username: true,
        name: true,
      },
    })

    if (!admin) {
      return NextResponse.json({ error: 'Admin not found' }, { status: 401 })
    }

    return NextResponse.json({ admin })
  } catch (error) {
    console.error('Auth check error:', error)
    return NextResponse.json({ error: 'Server error' }, { status: 500 })
  }
}

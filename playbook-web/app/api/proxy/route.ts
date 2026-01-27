import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const path = searchParams.get('path') || ''

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const path = searchParams.get('path') || ''
  const body = await request.json()

  try {
    const response = await fetch(`${BACKEND_URL}${path}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    return NextResponse.json(
      { error: 'Failed to fetch from backend' },
      { status: 500 }
    )
  }
}

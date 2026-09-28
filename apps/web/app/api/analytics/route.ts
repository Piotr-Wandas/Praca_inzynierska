import { NextRequest, NextResponse } from 'next/server';

const API = process.env.INTERNAL_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://api:8000';

export async function GET(request: NextRequest) {
  const incoming = request.nextUrl.searchParams;
  const mode = incoming.get('mode') === 'catalog' ? 'catalog' : 'overview';
  const params = new URLSearchParams(incoming);
  params.delete('mode');
  const target = `${API}/api/v1/analytics/${mode}${params.size ? `?${params.toString()}` : ''}`;
  try {
    const response = await fetch(target, { cache: 'no-store' });
    const body = await response.text();
    return new NextResponse(body, {
      status: response.status,
      headers: { 'content-type': response.headers.get('content-type') || 'application/json' },
    });
  } catch (error) {
    return NextResponse.json({ detail: `Błąd połączenia z API: ${String(error)}` }, { status: 502 });
  }
}

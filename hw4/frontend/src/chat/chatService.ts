// The chat window talks to the agent only through this file (POST /api/chat).
// Types mirror backend/models.py. Product cards are built by the backend from
// database rows, so prices and pictures never come from the AI model's text.

export type ChatRole = 'user' | 'assistant'

export interface ChatMessage {
  role: ChatRole
  content: string
  products?: ProductCard[]
  search?: SearchSummary | null
  blocked?: boolean // the sensitive-info guard stopped the shopper's message
}

// Present when the cards are search results (see backend/models.py SearchSummary).
export interface SearchSummary {
  query: string
  total_matches: number
  shown: number
}

export interface ProductCard {
  product_id: string
  name: string
  price: number
  image_url: string
  short_info: string
}

interface ChatReply {
  reply: string
  products: ProductCard[]
  search: SearchSummary | null
  blocked: boolean
}

export interface ChatContext {
  path: string // the page the shopper is on, e.g. /products/basic-hoodie-big-yale
  productId: string | null // the product on that page, if any (the server re-checks it)
}

const HISTORY_SENT = 12 // recent turns sent along (used for guests; logged-in history comes from the server)

const FRIENDLY_ERROR =
  'Sorry, I’m having trouble connecting right now. Please try again in a moment.'

export async function sendChatMessage(
  history: ChatMessage[],
  context: ChatContext,
): Promise<ChatMessage> {
  const latest = history[history.length - 1]
  const earlier = history.slice(0, -1).slice(-HISTORY_SENT).map((m) => ({
    role: m.role,
    content: m.content.slice(0, 2000),
    product_ids: (m.products ?? []).slice(0, 12).map((p) => p.product_id),
  }))
  let res: Response
  try {
    res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: latest.content,
        history: earlier,
        page: context.path,
        product_id: context.productId,
      }),
    })
  } catch {
    throw new Error(FRIENDLY_ERROR) // network down or backend not running
  }
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new Error(typeof data?.detail === 'string' ? data.detail : FRIENDLY_ERROR)
  }
  const reply = data as ChatReply
  return { role: 'assistant', content: reply.reply, products: reply.products, search: reply.search, blocked: reply.blocked }
}

// Saved history for the logged-in shopper (the server knows who from the login cookie).
export async function fetchHistory(): Promise<ChatMessage[]> {
  const res = await fetch('/api/chat/history')
  if (!res.ok) return []
  const rows = (await res.json()) as { role: ChatRole; content: string; products: ProductCard[]; search: SearchSummary | null }[]
  return rows.map((r) => ({ role: r.role, content: r.content, products: r.products, search: r.search }))
}

export async function clearHistory(): Promise<void> {
  const res = await fetch('/api/chat/history', { method: 'DELETE' })
  if (!res.ok) throw new Error('Couldn’t clear your chat. Please try again.')
}

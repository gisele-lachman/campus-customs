import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, matchPath, useLocation, useNavigate } from 'react-router-dom'
import { fetchProduct, formatPrice } from '../api'
import { useAuth } from '../auth/AuthContext'
import { useChatResults } from '../chat/ChatResultsContext'
import { OPEN_CHAT_EVENT } from '../chat/openChat'
import { Bulldog } from './Graphics'
import {
  clearHistory,
  fetchHistory,
  sendChatMessage,
  type ChatMessage as BaseMessage,
} from '../chat/chatService'

type ChatMessage = BaseMessage & { error?: boolean; greeting?: boolean; hidden?: boolean }

const HIDDEN_TEXT = '[Hidden for your safety: this message wasn’t sent or saved]'

// Tappable examples shown while the chat is empty.
const GENERAL_SUGGESTIONS = [
  'What hoodies do you have?',
  'Is the Basic Hoodie Big Yale in stock?',
  'Anything with a bulldog on it?',
  'Which is cheaper, the Morse 1/4 Zip or the Berkeley 1/4 Zip?',
]
const productSuggestions = (name: string) => [
  'Do you have this in my size?',
  'What colors does this come in?',
  `How much is the ${name}?`,
  'Do you have anything similar?',
]

const PREVIEW_COUNT = 3 // small thumbnails inside the chat; the full set goes on the page

const greeting = (firstName?: string | null): ChatMessage => ({
  role: 'assistant',
  greeting: true,
  content: firstName
    ? `Woof, welcome back, ${firstName}! 🐾 I’m the Campus Customs Bulldog. What Yale gear are we hunting for today?`
    : 'Woof, hi there! 🐾 I’m the Campus Customs Bulldog, your shopping sidekick. Ask me about styles, sizes, stock, or prices!',
})

export default function ChatWidget() {
  const { user, loading } = useAuth()
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting()])
  const [draft, setDraft] = useState('')
  const [waiting, setWaiting] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const chatResults = useChatResults()
  const bottomRef = useRef<HTMLDivElement>(null)

  // Other parts of the site (e.g. "Ask the Bulldog" buttons) can open the chat.
  useEffect(() => {
    const handler = () => setOpen(true)
    window.addEventListener(OPEN_CHAT_EVENT, handler)
    return () => window.removeEventListener(OPEN_CHAT_EVENT, handler)
  }, [])
  const productId = matchPath('/products/:productId', location.pathname)?.params.productId ?? null
  const [productName, setProductName] = useState<string | null>(null)
  useEffect(() => {
    setProductName(null)
    if (productId) fetchProduct(productId).then((p) => setProductName(p.name)).catch(() => setProductName(null))
  }, [productId])

  // Changes whenever the shopper logs in or out, so late replies from the old session are dropped.
  const sessionRef = useRef(0)

  // New shopper (log in, log out, or page refresh): start fresh, then load their own saved chat.
  // A guest conversation never carries over into an account, and logging out empties the window.
  const userId = user?.id ?? null
  useEffect(() => {
    if (loading) return
    const session = ++sessionRef.current
    setMessages([greeting(user?.first_name)])
    setWaiting(false)
    chatResults.clear()
    if (userId !== null) {
      fetchHistory().then((saved) => {
        if (sessionRef.current === session && saved.length) {
          setMessages([greeting(user?.first_name), ...saved])
        }
      })
    }
  }, [userId, loading])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, waiting, open])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    send(draft)
  }

  async function send(raw: string) {
    const text = raw.trim()
    if (!text || waiting) return
    const session = sessionRef.current
    const history = [...messages, { role: 'user' as const, content: text }]
    setMessages(history)
    setDraft('')
    setWaiting(true)
    // Greetings, error bubbles, and hidden (blocked) messages aren't part of the real conversation.
    const conversation = history.filter((m) => !m.greeting && !m.error && !m.hidden)
    try {
      const reply = await sendChatMessage(conversation, { path: location.pathname, productId })
      if (sessionRef.current !== session) return
      if (reply.blocked) {
        // Blank out what the shopper typed, so it isn't shown or sent again with later messages.
        setMessages((prev) => [
          ...prev.slice(0, -1),
          { role: 'user', content: HIDDEN_TEXT, hidden: true },
          { role: 'assistant', content: reply.content },
        ])
        return
      }
      setMessages((prev) => [...prev, reply])
      // Search results go on the Products page; take the shopper there if needed.
      // A search that found nothing clears old results so the page isn't stale.
      if (reply.search && reply.products?.length) {
        chatResults.show(reply.search, reply.products)
        if (location.pathname !== '/products') navigate('/products')
      } else if (reply.search) {
        chatResults.clear()
      }
    } catch (e) {
      if (sessionRef.current !== session) return
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: (e as Error).message, error: true },
      ])
    } finally {
      if (sessionRef.current === session) setWaiting(false)
    }
  }

  async function handleClear() {
    const message = user
      ? 'Delete your saved chat history? This can’t be undone.'
      : 'Clear this conversation?'
    if (!window.confirm(message)) return
    try {
      if (user) await clearHistory()
      setMessages([greeting(user?.first_name)])
      chatResults.clear()
    } catch (e) {
      setMessages((prev) => [...prev, { role: 'assistant', content: (e as Error).message, error: true }])
    }
  }

  const hasConversation = messages.some((m) => !m.greeting)

  return (
    <div className="chat">
      {open && (
        <section className="chat-window" aria-label="Shopping assistant">
          <header className="chat-header">
            <div className="chat-ident">
              <Bulldog className="avatar" />
              <div>
                <div className="chat-title">The Campus Customs Bulldog</div>
                <div className="chat-sub">Checking the real shelves for you</div>
              </div>
            </div>
            <div className="chat-header-actions">
              {hasConversation && (
                <button type="button" className="chat-clear" onClick={handleClear}>
                  Clear my chat
                </button>
              )}
              <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}${m.error ? ' error' : ''}${m.hidden ? ' hidden-msg' : ''}`}>
                {m.content}
                {m.products && m.products.length > 0 && (
                  <div className="chat-preview">
                    {m.products.slice(0, PREVIEW_COUNT).map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-preview-item">
                        <img src={p.image_url} alt="" />
                        <span>{p.name}</span>
                        <span className="price">{formatPrice(p.price)}</span>
                      </Link>
                    ))}
                    <button
                      type="button"
                      className="chat-preview-all"
                      onClick={() => {
                        const n = m.products!.length
                        chatResults.show(m.search ?? { query: 'earlier chat', total_matches: n, shown: n }, m.products!)
                        navigate('/products')
                      }}
                    >
                      See all {m.products.length} on the Products page →
                    </button>
                  </div>
                )}
              </div>
            ))}
            {!hasConversation && !waiting && (
              <div className="chat-suggestions" aria-label="Suggested questions">
                <span className="muted">Fetch me an answer to…</span>
                {(productId && productName ? productSuggestions(productName) : GENERAL_SUGGESTIONS).map((q) => (
                  <button key={q} type="button" className="chat-suggestion" onClick={() => send(q)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
            {waiting && (
              <div className="chat-bubble assistant typing" role="status">
                <span className="dot" />
                <span className="dot" />
                <span className="dot" />
                <span className="typing-label">sniffing out an answer…</span>
                <span className="sr-only">typing…</span>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Ask the Bulldog about sizes, colors, prices…"
              aria-label="Chat message"
              maxLength={2000}
              autoFocus
            />
            <button type="submit" disabled={!draft.trim() || waiting}>
              Send
            </button>
          </form>
        </section>
      )}
      <button
        type="button"
        className={`chat-toggle${open ? ' open' : ''}`}
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? (
          '×'
        ) : (
          <>
            <Bulldog className="avatar wiggle" />
            <span className="label">Ask the Bulldog</span>
          </>
        )}
      </button>
    </div>
  )
}

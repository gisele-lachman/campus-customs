import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ProductCard, SearchSummary } from './chatService'

// The latest search results from the chat, shown on the Products page.
export interface ChatResults extends SearchSummary {
  products: ProductCard[]
  id: number // changes on every new search, so the page can react
  source: 'chat' | 'browse' // from the chat, or from a Home page shortcut like "Shop by college"
}

interface ChatResultsState {
  results: ChatResults | null
  show: (summary: SearchSummary, products: ProductCard[], source?: 'chat' | 'browse') => void
  clear: () => void
}

const ChatResultsContext = createContext<ChatResultsState | null>(null)

export function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResults] = useState<ChatResults | null>(null)
  const value: ChatResultsState = {
    results,
    show: (summary, products, source = 'chat') => setResults({ ...summary, products, source, id: Date.now() }),
    clear: () => setResults(null),
  }
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}

export function useChatResults(): ChatResultsState {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}

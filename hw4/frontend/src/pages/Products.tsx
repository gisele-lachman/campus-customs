import { useEffect, useMemo, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import { useChatResults } from '../chat/ChatResultsContext'
import { EmptyPennant } from '../components/Graphics'
import ProductCard from '../components/ProductCard'
import { SkeletonGrid } from '../components/Skeletons'
import ProductFilters, { applyFilters, NO_FILTERS, type Filters } from '../components/ProductFilters'

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const location = useLocation()
  // A Home page category tile can open this page with a type already chosen.
  const presetType = (location.state as { type?: string } | null)?.type ?? ''
  const [filters, setFilters] = useState<Filters>({ ...NO_FILTERS, type: presetType })
  const { results, clear } = useChatResults()

  useEffect(() => {
    fetchProducts().then(setProducts).catch((e: Error) => setError(e.message))
  }, [])

  // New chat results: start them unfiltered (so nothing is hidden) and scroll to the banner.
  useEffect(() => {
    if (results) {
      setFilters(NO_FILTERS)
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }, [results])

  // What's being browsed: chat results (in best-match order) or the whole catalogue.
  const base = useMemo(() => {
    if (!products) return []
    if (!results) return products
    const byId = new Map(products.map((p) => [p.product_id, p]))
    return results.products.map((c) => byId.get(c.product_id)).filter((p): p is Product => !!p)
  }, [products, results])
  const visible = useMemo(() => applyFilters(base, filters), [base, filters])

  if (error) return <p className="error">Couldn’t load products ({error}). Is the backend running?</p>

  return (
    <>
      {results ? (
        <div className="chat-results-banner" role="status">
          <div>
            <strong>{results.source === 'chat' ? 'Showing results from your chat:' : 'Showing results for'}</strong> “{results.query}”
            <div className="muted">
              {results.total_matches > results.shown
                ? `Found ${results.total_matches} items, showing the top ${results.shown}.`
                : `Found ${results.total_matches} ${results.total_matches === 1 ? 'item' : 'items'}.`}
            </div>
          </div>
          <button type="button" className="button" onClick={clear}>
            Back to all products
          </button>
        </div>
      ) : (
        <div className="shop-head">
          <span className="kicker">The full roster</span>
          <h1>Shop All</h1>
          <p className="muted">
            Every hoodie, crewneck, quarter-zip, and tee we carry. Narrow it down below, or ask the Bulldog in the corner.
          </p>
        </div>
      )}

      {!products ? (
        <SkeletonGrid />
      ) : (
      <>
      <ProductFilters list={base} filters={filters} onChange={setFilters} shown={visible.length} />

      {visible.length === 0 ? (
        <div className="no-results">
          <EmptyPennant />
          <p>No items match these filters. Try a different color or size, or clear the filters.</p>
          <button type="button" className="button" onClick={() => setFilters({ ...NO_FILTERS, sort: filters.sort })}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="product-grid">
          {visible.map((p, i) => (
            <ProductCard key={p.product_id} product={p} index={i} />
          ))}
        </div>
      )}
      </>
      )}
    </>
  )
}

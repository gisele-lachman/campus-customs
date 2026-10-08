import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchProducts, formatPrice, type Product } from '../api'
import { useChatResults } from '../chat/ChatResultsContext'
import type { ProductCard as Card, SearchSummary } from '../chat/chatService'
import { openChat } from '../chat/openChat'
import { Badge, Bulldog, Pennant } from '../components/Graphics'
import ProductCard from '../components/ProductCard'
import { SkeletonGrid } from '../components/Skeletons'

// Residential colleges we look for in product names (only ones with real products are shown).
const COLLEGES = [
  'Benjamin Franklin', 'Berkeley', 'Branford', 'Davenport', 'Ezra Stiles', 'Grace Hopper', 'Jonathan Edwards',
  'Morse', 'Pauli Murray', 'Pierson', 'Saybrook', 'Silliman', 'Timothy Dwight', 'Trumbull',
]
const TYPE_ORDER = ['Hoodies', 'Crewnecks', 'T-Shirts', 'Quarter-Zips', 'Jackets & Fleece', 'Long Sleeves']
const HERO_PRODUCT = 'basic-hoodie-big-yale'

interface SearchResponse {
  search: SearchSummary
  products: Card[]
}
const browseSearch = (q: string) =>
  fetch(`/api/search?q=${encodeURIComponent(q)}`).then((r) => r.json() as Promise<SearchResponse>)

export default function Home() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [pride, setPride] = useState<SearchResponse | null>(null)
  const navigate = useNavigate()
  const chatResults = useChatResults()

  useEffect(() => {
    fetchProducts().then(setProducts).catch(() => setProducts([]))
    browseSearch('bulldog').then(setPride).catch(() => setPride(null))
  }, [])

  const data = useMemo(() => {
    if (!products?.length) return null
    const byStock = [...products].sort((a, b) => b.total_stock - a.total_stock)
    const categories = TYPE_ORDER.map((t) => {
      const items = byStock.filter((p) => p.type_group === t)
      return { name: t, count: items.length, image: items[0]?.image_url }
    }).filter((c) => c.count > 0)
    const colleges = COLLEGES.filter((c) => products.some((p) => p.name.startsWith(c)))
    return {
      hero: products.find((p) => p.product_id === HERO_PRODUCT) ?? byStock[0],
      categories,
      colleges,
      fullRun: byStock.filter((p) => p.in_stock_sizes.length === 6).slice(0, 4),
      lowest: Math.min(...products.map((p) => p.price)),
    }
  }, [products])

  // Show search results on the Products page, with a banner, like a chat search.
  async function browse(q: string) {
    const r = await browseSearch(q)
    if (r.products.length) {
      chatResults.show(r.search, r.products, 'browse')
      navigate('/products')
    }
  }

  return (
    <>
      <section className="hero">
        <div className="reveal">
          <span className="kicker">Campus Customs · New Haven</span>
          <h1>
            Old-school spirit. <em>Brand-new</em> favorites.
          </h1>
          <p>
            Vintage-varsity Yale gear for the lecture hall, the stands at the Bowl, and every reunion after. Find your
            college, your sport, and your size.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="button gold">Shop the collection</Link>
            <button type="button" className="button-ghost" onClick={openChat}>Ask the Bulldog</button>
          </div>
        </div>
        <div className="hero-art reveal d2">
          <Pennant className="hero-pennant" />
          {data?.hero && (
            <>
              <div className="hero-photo">
                <img src={data.hero.image_url} alt={data.hero.name} />
              </div>
              <Link to={`/products/${data.hero.product_id}`} className="hero-photo-caption">
                {data.hero.name} · {formatPrice(data.hero.price)}
              </Link>
            </>
          )}
          <Badge className="hero-badge" />
        </div>
      </section>

      {data && (
        <div className="scoreboard reveal d3" aria-label="Shop at a glance">
          <div className="score"><span className="score-num">{products!.length}</span><span className="score-label">Styles in stock</span></div>
          <div className="score"><span className="score-num">{data.colleges.length}</span><span className="score-label">Residential colleges</span></div>
          <div className="score"><span className="score-num">XS–XXL</span><span className="score-label">Size range</span></div>
          <div className="score"><span className="score-num">{formatPrice(data.lowest).replace('.00', '')}</span><span className="score-label">Starting price</span></div>
        </div>
      )}

      <section className="section">
        <div className="section-head">
          <div>
            <span className="kicker">Pick your position</span>
            <h2>Shop by category</h2>
          </div>
          <Link to="/products" className="link-button">See everything →</Link>
        </div>
        {data ? (
          <div className="category-grid">
            {data.categories.map((c) => (
              <button key={c.name} type="button" className="category-tile" onClick={() => { chatResults.clear(); navigate('/products', { state: { type: c.name } }) }}>
                {c.image && <img src={c.image} alt="" loading="lazy" />}
                <span className="category-name">{c.name}</span>
                <span className="category-count">{c.count} styles</span>
              </button>
            ))}
          </div>
        ) : (
          <SkeletonGrid count={4} />
        )}
      </section>

      <section className="section college-band">
        <span className="kicker">Home colors</span>
        <h2>Rep your residential college</h2>
        <p className="muted">
          Crewnecks, quarter-zips, and tees for {data?.colleges.length ?? 'our'} colleges. Tap yours to see what we carry.
        </p>
        <div className="college-list">
          {data?.colleges.map((c) => (
            <button key={c} type="button" className="college-chip" onClick={() => browse(c)}>
              <span className="dot">{c[0]}</span>
              {c}
            </button>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <div>
            <span className="kicker">Ready when you are</span>
            <h2>Stocked in every size</h2>
            <p className="muted" style={{ margin: 0 }}>Our deepest-stocked styles, available from XS to XXL right now.</p>
          </div>
        </div>
        {data ? (
          <div className="product-grid">
            {data.fullRun.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}
          </div>
        ) : (
          <SkeletonGrid count={4} />
        )}
      </section>

      {pride && pride.products.length > 0 && (
        <section className="section pride">
          <div>
            <Bulldog className="pride-art" />
            <span className="kicker">Bulldog pride</span>
            <h2>Bring the bark</h2>
            <p>
              {pride.search.total_matches} pieces with a bulldog on them, from vintage sailor pups to standing mascots.
              Built for game days and lazy Sundays alike.
            </p>
            <button type="button" className="button gold" onClick={() => browse('bulldog')}>
              See all {pride.search.total_matches}
            </button>
          </div>
          <div className="pride-grid">
            {pride.products.slice(0, 4).map((p, i) => (
              <ProductCard key={p.product_id} product={{ ...p, short_description: p.short_info }} index={i} />
            ))}
          </div>
        </section>
      )}

      <section className="section chat-cta">
        <div>
          <span className="kicker">Not sure where to start?</span>
          <h2>Ask the Bulldog</h2>
          <p className="muted">Sizes, stock, colors, or “which is cheaper?” Our shopping assistant checks the real shelves.</p>
        </div>
        <button type="button" className="button" onClick={openChat}>Start a chat</button>
      </section>
    </>
  )
}

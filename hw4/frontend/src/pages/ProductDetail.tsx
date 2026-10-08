import { useEffect, useState, type MouseEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail as Detail } from '../api'
import { SkeletonDetail } from '../components/Skeletons'
import { openChat } from '../chat/openChat'

const LOW_STOCK = 5 // "Only N left" at or below this

// Swatch colors for the color names used in the catalogue (display only).
const SWATCHES: Record<string, string> = {
  black: '#1b1b1b', blue: '#2f5fa8', 'charcoal gray': '#4a4f57', cream: '#f1e6cc',
  'dark heather charcoal': '#3f434a', 'dark heather gray': '#5d6168', 'dusty coral': '#d98b7a',
  gold: '#c9a227', gray: '#9a9ea5', green: '#2f6b3f', 'heather charcoal gray': '#55595f',
  'heather gray': '#b7b9bd', ivory: '#fbf6e6', 'light blue': '#9cc4ec', 'light gray': '#d4d6d9',
  multicolor: 'conic-gradient(#00356b, #c4962c, #a3352b, #2f6b3f, #00356b)', navy: '#14254a',
  'navy blue': '#14254a', red: '#b3261e', 'royal blue': '#2a52be', white: '#ffffff', yellow: '#f2c94c',
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  const [product, setProduct] = useState<Detail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setProduct(null)
    setError(null)
    fetchProduct(productId).then(setProduct).catch((e: Error) => setError(e.message))
  }, [productId])

  // Zoom follows the mouse on the large image.
  function handleZoom(e: MouseEvent<HTMLDivElement>) {
    const r = e.currentTarget.getBoundingClientRect()
    e.currentTarget.style.setProperty('--zx', `${((e.clientX - r.left) / r.width) * 100}%`)
    e.currentTarget.style.setProperty('--zy', `${((e.clientY - r.top) / r.height) * 100}%`)
  }

  if (error) {
    return (
      <div className="no-results">
        <h2>We couldn’t find that item</h2>
        <p className="muted">({error})</p>
        <Link to="/products" className="button">Back to all products</Link>
      </div>
    )
  }
  if (!product) return <SkeletonDetail />

  const inStock = product.inventory.filter((s) => s.quantity > 0)
  const lowest = Math.min(...inStock.map((s) => s.quantity))

  return (
    <>
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/">Home</Link> <span>/</span> <Link to="/products">Products</Link> <span>/</span>
        <span>{product.name}</span>
      </nav>
      <div className="detail">
        <div className="detail-media" onMouseMove={handleZoom}>
          <img className="detail-image" src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info reveal">
          <span className="kicker">{product.type_group}</span>
          <h1>{product.name}</h1>
          <div className="detail-price">
            <span className="price large">{formatPrice(product.price)}</span>
            {inStock.length === 0 ? (
              <span className="stock-pill low">Sold out in every size</span>
            ) : (
              <span className={`stock-pill${lowest <= LOW_STOCK ? ' low' : ''}`}>
                In stock in {inStock.length} of {product.inventory.length} sizes
              </span>
            )}
          </div>
          <p className="description">{product.description}</p>

          <section className="detail-block">
            <h2>Colors</h2>
            <ul className="swatches">
              {product.colors.map((c) => (
                <li key={c}>
                  <span className="swatch" style={{ background: SWATCHES[c] ?? '#ccc' }} />
                  {c}
                </li>
              ))}
            </ul>
          </section>

          <section className="detail-block">
            <h2>Stock by size</h2>
            <ul className="size-grid stock-table">
              {product.inventory.map(({ size, quantity }) => {
                const state = quantity === 0 ? 'sold-out' : quantity <= LOW_STOCK ? 'low' : 'in'
                return (
                  <li key={size} className={`size-tile ${state}`} aria-label={quantity === 0 ? `${size}: sold out` : `${size}: ${quantity} in stock`}>
                    <span className="size">{size}</span>
                    <span className="qty">
                      {quantity === 0 ? 'Sold out' : quantity <= LOW_STOCK ? `Only ${quantity} left` : `${quantity} in stock`}
                    </span>
                  </li>
                )
              })}
            </ul>
            <div className="size-legend">
              <span className="l-in">In stock</span>
              <span className="l-low">Only a few left</span>
              <span className="l-out">Sold out</span>
            </div>
          </section>

          <div className="ask-row">
            <button type="button" className="button" onClick={openChat}>
              Ask the Bulldog about this
            </button>
            <Link to="/products" className="button-ghost">
              Keep browsing
            </Link>
          </div>
        </div>
      </div>
    </>
  )
}

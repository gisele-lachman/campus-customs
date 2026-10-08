import { Link } from 'react-router-dom'
import { formatPrice, SIZES } from '../api'

// The fields a card needs. Catalogue products and chat/browse results both provide them;
// the extra fields (type, sizes) show when available.
export interface CardData {
  product_id: string
  name: string
  price: number
  image_url: string
  short_description: string
  type_group?: string
  in_stock_sizes?: string[]
}

export default function ProductCard({ product, index = 0 }: { product: CardData; index?: number }) {
  return (
    <Link
      to={`/products/${product.product_id}`}
      className="product-card"
      style={{ animationDelay: `${Math.min(index, 11) * 40}ms` }}
    >
      <div className="product-media">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="price-tag">{formatPrice(product.price)}</span>
      </div>
      <div className="product-card-body">
        {product.type_group && <span className="kicker">{product.type_group}</span>}
        <h3>{product.name}</h3>
        <p className="price sr-only">{formatPrice(product.price)}</p>
        <p className="muted">{product.short_description}</p>
        {product.in_stock_sizes && (
          <div className="card-sizes" aria-label="Sizes in stock">
            {SIZES.map((s) => {
              const inStock = product.in_stock_sizes!.includes(s)
              return (
                <span key={s} className={`card-size${inStock ? '' : ' out'}`} title={inStock ? `${s} in stock` : `${s} sold out`}>
                  {s}
                </span>
              )
            })}
          </div>
        )}
      </div>
    </Link>
  )
}

// Types and fetch helpers for the FastAPI backend (see backend/main.py).

export interface Product {
  product_id: string
  name: string // tidied display name
  raw_name: string // name exactly as stored in the database
  garment_type: string
  description: string
  short_description: string
  colors: string[]
  search_tags: string[]
  image_url: string
  price: number
  total_stock: number
  in_stock_sizes: string[] // sizes with at least one unit
  type_group: string // clean filter group, e.g. "Hoodies" (backend/categories.py)
  color_groups: string[] // clean color groups, e.g. ["Navy", "White & Cream"]
}

export interface SizeStock {
  size: string
  quantity: number
}

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

export interface ProductDetail extends Product {
  inventory: SizeStock[]
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json() as Promise<T>
}

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (productId: string) =>
  getJson<ProductDetail>(`/api/products/${encodeURIComponent(productId)}`)

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

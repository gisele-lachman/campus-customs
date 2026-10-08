import { SIZES, type Product } from '../api'

export type SortOrder = 'featured' | 'price-asc' | 'price-desc'

export interface Filters {
  type: string // '' = any
  color: string // '' = any
  stock: string // '' = all items, 'any' = in stock in any size, or a size like 'M'
  sort: SortOrder
}

export const NO_FILTERS: Filters = { type: '', color: '', stock: '', sort: 'featured' }

const TYPE_ORDER = ['Hoodies', 'Crewnecks', 'T-Shirts', 'Quarter-Zips', 'Long Sleeves', 'Jackets & Fleece', 'Other']

function matches(p: Product, f: Filters, skip?: keyof Filters): boolean {
  if (skip !== 'type' && f.type && p.type_group !== f.type) return false
  if (skip !== 'color' && f.color && !p.color_groups.includes(f.color)) return false
  if (skip !== 'stock' && f.stock) {
    if (f.stock === 'any' ? p.in_stock_sizes.length === 0 : !p.in_stock_sizes.includes(f.stock)) return false
  }
  return true
}

/** Filter and sort a list. "featured" keeps the incoming order (A–Z, or best match for chat results). */
export function applyFilters(list: Product[], f: Filters): Product[] {
  const out = list.filter((p) => matches(p, f))
  if (f.sort === 'price-asc') out.sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
  if (f.sort === 'price-desc') out.sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
  return out
}

export const isFiltered = (f: Filters) => !!(f.type || f.color || f.stock)

interface Props {
  list: Product[] // the items being browsed (all products, or chat results)
  filters: Filters
  onChange: (f: Filters) => void
  shown: number
}

export default function ProductFilters({ list, filters, onChange, shown }: Props) {
  // Each option's count reflects the other active filters, so a count is what you'd get by choosing it.
  const count = (key: keyof Filters, test: (p: Product) => boolean) =>
    list.filter((p) => matches(p, filters, key) && test(p)).length
  const types = TYPE_ORDER.filter((t) => list.some((p) => p.type_group === t))
  const colors = [...new Set(list.flatMap((p) => p.color_groups))].sort()
  const set = (patch: Partial<Filters>) => onChange({ ...filters, ...patch })

  return (
    <div className="filters" role="search" aria-label="Filter products">
      <label>
        Type
        <select value={filters.type} onChange={(e) => set({ type: e.target.value })}>
          <option value="">All types ({count('type', () => true)})</option>
          {types.map((t) => (
            <option key={t} value={t}>
              {t} ({count('type', (p) => p.type_group === t)})
            </option>
          ))}
        </select>
      </label>
      <label>
        Color
        <select value={filters.color} onChange={(e) => set({ color: e.target.value })}>
          <option value="">All colors ({count('color', () => true)})</option>
          {colors.map((c) => (
            <option key={c} value={c}>
              {c} ({count('color', (p) => p.color_groups.includes(c))})
            </option>
          ))}
        </select>
      </label>
      <label>
        Availability
        <select value={filters.stock} onChange={(e) => set({ stock: e.target.value })}>
          <option value="">All items ({count('stock', () => true)})</option>
          <option value="any">In stock only ({count('stock', (p) => p.in_stock_sizes.length > 0)})</option>
          {SIZES.map((s) => (
            <option key={s} value={s}>
              In stock in {s} ({count('stock', (p) => p.in_stock_sizes.includes(s))})
            </option>
          ))}
        </select>
      </label>
      <label>
        Sort
        <select value={filters.sort} onChange={(e) => set({ sort: e.target.value as SortOrder })}>
          <option value="featured">Featured</option>
          <option value="price-asc">Price: low to high</option>
          <option value="price-desc">Price: high to low</option>
        </select>
      </label>
      <div className="filters-summary">
        <span className="filters-count">
          Showing {shown} of {list.length} items
        </span>
        {isFiltered(filters) && (
          <button type="button" className="link-button" onClick={() => onChange({ ...NO_FILTERS, sort: filters.sort })}>
            Clear filters
          </button>
        )}
      </div>
    </div>
  )
}

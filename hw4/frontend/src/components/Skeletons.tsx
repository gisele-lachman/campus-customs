// Shimmering placeholders shown while products load.
export function SkeletonGrid({ count = 8 }: { count?: number }) {
  return (
    <div className="product-grid" aria-busy="true" aria-label="Loading products">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="skeleton-card">
          <div className="skeleton media" />
          <div className="lines">
            <div className="skeleton line short" />
            <div className="skeleton line mid" />
            <div className="skeleton line" />
          </div>
        </div>
      ))}
    </div>
  )
}

export function SkeletonDetail() {
  return (
    <div className="detail" aria-busy="true" aria-label="Loading product">
      <div className="skeleton" style={{ aspectRatio: '1', borderRadius: 22 }} />
      <div style={{ display: 'grid', gap: 14 }}>
        <div className="skeleton line short" />
        <div className="skeleton" style={{ height: 44 }} />
        <div className="skeleton" style={{ height: 32, width: '30%' }} />
        <div className="skeleton line" />
        <div className="skeleton line mid" />
        <div className="skeleton" style={{ height: 70 }} />
      </div>
    </div>
  )
}

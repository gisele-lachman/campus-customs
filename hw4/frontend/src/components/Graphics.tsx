// Small hand-drawn SVG graphics for the varsity theme. No real Yale logos or crests:
// just a "CC" felt-letter monogram, a shop pennant, a circular badge, and a cartoon bulldog.

export function Monogram({ size = 44 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <circle cx="32" cy="32" r="29" fill="#fffaf0" stroke="#e0b44a" strokeWidth="4" />
      <circle cx="32" cy="32" r="23" fill="none" stroke="#00356b" strokeWidth="1.5" strokeDasharray="3 3" />
      <text x="32" y="42" textAnchor="middle" fontFamily="Graduate, Georgia, serif" fontSize="25" fill="#00356b">
        CC
      </text>
    </svg>
  )
}

export function Pennant({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 240 110" aria-hidden="true">
      <rect x="0" y="6" width="12" height="98" rx="4" fill="#c4962c" />
      <path d="M12 8 L236 55 L12 102 Z" fill="#fffaf0" stroke="#e0b44a" strokeWidth="3" />
      <path d="M12 22 L170 55 L12 88 Z" fill="#00356b" />
      <text x="20" y="60" fontFamily="Graduate, Georgia, serif" fontSize="15" fill="#fffaf0" letterSpacing="1">
        CUSTOMS
      </text>
    </svg>
  )
}

export function Badge({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 120 120" aria-hidden="true">
      <defs>
        <path id="badge-circle" d="M60 60 m-44 0 a44 44 0 1 1 88 0 a44 44 0 1 1 -88 0" />
      </defs>
      <circle cx="60" cy="60" r="57" fill="#e0b44a" />
      <circle cx="60" cy="60" r="50" fill="#00254a" />
      <text fontFamily="Libre Franklin, sans-serif" fontWeight="700" fontSize="10.5" letterSpacing="2.4" fill="#fffaf0">
        <textPath href="#badge-circle">VINTAGE VARSITY · NEW HAVEN · CAMPUS CUSTOMS ·</textPath>
      </text>
      <text x="60" y="70" textAnchor="middle" fontFamily="Graduate, Georgia, serif" fontSize="28" fill="#e0b44a">
        CC
      </text>
    </svg>
  )
}

/** A friendly cartoon bulldog face, drawn from simple shapes. */
export function Bulldog({ className, size }: { className?: string; size?: number }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 100 100" aria-hidden="true">
      <circle cx="50" cy="50" r="48" fill="#fffaf0" stroke="#e0b44a" strokeWidth="4" />
      {/* ears */}
      <path d="M18 34 Q14 14 34 20 Q30 30 26 38 Z" fill="#00356b" />
      <path d="M82 34 Q86 14 66 20 Q70 30 74 38 Z" fill="#00356b" />
      {/* head */}
      <ellipse cx="50" cy="54" rx="31" ry="27" fill="#e9dcc2" stroke="#00356b" strokeWidth="2.5" />
      {/* brow wrinkles */}
      <path d="M40 36 Q50 32 60 36" fill="none" stroke="#a8946d" strokeWidth="2" strokeLinecap="round" />
      {/* eyes */}
      <circle cx="38" cy="47" r="4.5" fill="#0d1f3a" />
      <circle cx="62" cy="47" r="4.5" fill="#0d1f3a" />
      <circle cx="39.5" cy="45.5" r="1.4" fill="#fff" />
      <circle cx="63.5" cy="45.5" r="1.4" fill="#fff" />
      {/* muzzle */}
      <ellipse cx="50" cy="63" rx="17" ry="12" fill="#fffaf0" stroke="#00356b" strokeWidth="2" />
      <ellipse cx="50" cy="56.5" rx="6.5" ry="4.5" fill="#0d1f3a" />
      <path d="M50 61 L50 65 M41 67 Q50 73 59 67" fill="none" stroke="#0d1f3a" strokeWidth="2" strokeLinecap="round" />
      {/* underbite teeth */}
      <path d="M44 68.5 l2 -3 l2 3 M52 68.5 l2 -3 l2 3" fill="#fff" stroke="#0d1f3a" strokeWidth="1" />
      {/* collar */}
      <path d="M26 76 Q50 90 74 76" fill="none" stroke="#c4962c" strokeWidth="5" strokeLinecap="round" />
    </svg>
  )
}

/** Empty-state illustration: a deflated little pennant. */
export function EmptyPennant() {
  return (
    <svg viewBox="0 0 120 80" aria-hidden="true">
      <rect x="6" y="6" width="6" height="70" rx="3" fill="#c4962c" />
      <path d="M12 10 Q70 30 108 46 Q60 50 12 62 Z" fill="#ece3cd" stroke="#00356b" strokeWidth="2" strokeDasharray="4 3" />
      <text x="40" y="44" fontFamily="Graduate, Georgia, serif" fontSize="14" fill="#00356b">?</text>
    </svg>
  )
}

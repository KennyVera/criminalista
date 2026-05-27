import { useEffect, useRef, useState } from 'react'
import { ResponsiveContainer } from 'recharts'

/**
 * Evita avisos de Recharts (width/height -1) cuando el contenedor aun no tiene tamaño.
 */
export default function MeasuredChart({ className = 'h-72 w-full', children }) {
  const ref = useRef(null)
  const [size, setSize] = useState({ width: 0, height: 0 })

  useEffect(() => {
    const el = ref.current
    if (!el || typeof ResizeObserver === 'undefined') return undefined

    const update = () => {
      const { width, height } = el.getBoundingClientRect()
      const w = Math.floor(width)
      const h = Math.floor(height)
      if (w > 0 && h > 0) setSize({ width: w, height: h })
    }

    update()
    const ro = new ResizeObserver(update)
    ro.observe(el)
    return () => ro.disconnect()
  }, [])

  return (
    <div ref={ref} className={className}>
      {size.width > 0 && size.height > 0 ? (
        <ResponsiveContainer width={size.width} height={size.height} minWidth={0}>
          {children}
        </ResponsiveContainer>
      ) : null}
    </div>
  )
}

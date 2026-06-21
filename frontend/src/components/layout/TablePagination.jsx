import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '../ui'
import { cn } from '../../lib/cn'

export default function TablePagination({
  page,
  totalPages = 1,
  totalItems,
  perPage = 10,
  onPageChange,
  onPerPageChange,
  itemLabel = 'registros',
  className,
}) {
  const from = totalItems === 0 ? 0 : (page - 1) * perPage + 1
  const to = Math.min(page * perPage, totalItems ?? 0)

  return (
    <div className={cn('table-footer', className)}>
      <p className="text-xs sm:text-sm text-black">
        Mostrando{' '}
        <span className="font-bold text-black">
          {from === to ? from : `${from}–${to}`}
        </span>{' '}
        de{' '}
        <span className="font-bold text-black">
          {(totalItems ?? 0).toLocaleString('es-CO')}
        </span>{' '}
        {itemLabel}
      </p>
      <div className="flex flex-wrap items-center gap-2">
        {onPerPageChange && (
          <select
            value={perPage}
            onChange={(e) => onPerPageChange(Number(e.target.value))}
            className="rounded-lg border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-black"
            aria-label="Registros por página"
          >
            {[10, 20, 25, 50].map((n) => (
              <option key={n} value={n}>
                {n} por página
              </option>
            ))}
          </select>
        )}
        <div className="flex items-center gap-1">
          <Button
            variant="secondary"
            size="sm"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            aria-label="Página anterior"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <span className="min-w-[4.5rem] text-center text-xs font-medium">
            {page} / {totalPages || 1}
          </span>
          <Button
            variant="secondary"
            size="sm"
            disabled={page >= (totalPages || 1)}
            onClick={() => onPageChange(page + 1)}
            aria-label="Página siguiente"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  )
}

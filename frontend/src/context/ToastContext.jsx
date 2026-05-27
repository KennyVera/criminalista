import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import ToastContainer from '../components/ToastContainer'

const ToastContext = createContext(null)

let toastId = 0

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([])

  const dismiss = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const show = useCallback(
    (type, title, message = '', duration = 5000) => {
      const id = ++toastId
      setToasts((prev) => [...prev, { id, type, title, message }])
      if (duration > 0) {
        window.setTimeout(() => dismiss(id), duration)
      }
      return id
    },
    [dismiss]
  )

  const toast = useMemo(
    () => ({
      success: (title = 'Éxito', message = 'Guardado correctamente') =>
        show('success', title, message),
      error: (title = 'Error', message = 'Ocurrió un problema') =>
        show('error', title, message),
      warning: (title = 'Advertencia', message = '') => show('warning', title, message),
      info: (title = 'Información', message = '') => show('info', title, message),
      dismiss,
    }),
    [show, dismiss]
  )

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  )
}

export function useToast() {
  const ctx = useContext(ToastContext)
  if (!ctx) {
    throw new Error('useToast debe usarse dentro de ToastProvider')
  }
  return ctx
}

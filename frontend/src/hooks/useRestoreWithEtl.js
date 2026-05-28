import { useCallback, useRef, useState } from 'react'

const POLL_MS = 1500

export function useRestoreWithEtl({ startRestore, getStatus, cancelRestore }) {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState({
    percent: 0,
    message: '',
    phase: '',
  })
  const cancelRef = useRef(false)
  const taskIdRef = useRef(null)

  const run = useCallback(
    async (file) => {
      if (!file) throw new Error('Selecciona un archivo ZIP')
      cancelRef.current = false
      taskIdRef.current = null
      setRunning(true)
      setProgress({ percent: 0, message: 'Subiendo respaldo...', phase: 'init' })

      try {
        const queued = await startRestore(file)
        const taskId = queued.task_id
        if (!taskId) throw new Error('No se recibió identificador de tarea')
        taskIdRef.current = taskId

        const result = await new Promise((resolve, reject) => {
          const tick = async () => {
            if (cancelRef.current) {
              resolve({ cancelled: true })
              return
            }
            try {
              const st = await getStatus(taskId)
              setProgress({
                percent: st.percent ?? 0,
                message: st.message || st.phase || 'Procesando...',
                phase: st.phase || '',
              })
              if (st.status === 'completed') {
                resolve(st.result || st)
                return
              }
              if (st.status === 'cancelled' || st.status === 'cancelling') {
                if (st.status === 'cancelled') {
                  resolve({ cancelled: true, message: st.message })
                } else {
                  setTimeout(tick, POLL_MS)
                }
                return
              }
              if (st.status === 'failed') {
                reject(new Error(st.error || st.message || 'Restauración fallida'))
                return
              }
            } catch (err) {
              reject(err)
              return
            }
            setTimeout(tick, POLL_MS)
          }
          tick()
        })
        return result
      } finally {
        setRunning(false)
        taskIdRef.current = null
      }
    },
    [startRestore, getStatus]
  )

  const cancel = useCallback(async () => {
    if (!running || !taskIdRef.current || !cancelRestore) return
    cancelRef.current = true
    setProgress((p) => ({
      ...p,
      message: 'Solicitando cancelación…',
      phase: 'cancelling',
    }))
    try {
      await cancelRestore(taskIdRef.current)
    } catch {
      /* el polling reflejará el estado final */
    }
  }, [running, cancelRestore])

  return { run, running, progress, cancel, canCancel: running && !!cancelRestore }
}

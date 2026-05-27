import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { adminApi } from '../api/admin'

const AppConfigContext = createContext({
  appName: 'CrimeTrack Analytics',
  subtitle: 'Panel de analítica criminal — ISO 9241-210',
  iconUrl: '',
  reloadConfig: async () => {},
})

export function AppConfigProvider({ children }) {
  const [config, setConfig] = useState({
    appName: 'CrimeTrack Analytics',
    subtitle: 'Panel de analítica criminal — ISO 9241-210',
    iconUrl: '',
  })

  const reloadConfig = useCallback(async () => {
    try {
      const data = await adminApi.publicConfig()
      setConfig({
        appName: data.app_nombre || 'CrimeTrack Analytics',
        subtitle: data.app_subtitulo || 'Panel de analítica criminal — ISO 9241-210',
        iconUrl: data.app_icon_url || '',
      })
    } catch {
      /* silent fallback to current state */
    }
  }, [])

  useEffect(() => {
    reloadConfig()
  }, [reloadConfig])

  const value = useMemo(
    () => ({
      ...config,
      reloadConfig,
    }),
    [config, reloadConfig]
  )

  return <AppConfigContext.Provider value={value}>{children}</AppConfigContext.Provider>
}

export function useAppConfig() {
  const ctx = useContext(AppConfigContext)
  if (!ctx) {
    throw new Error('useAppConfig debe usarse dentro de AppConfigProvider')
  }
  return ctx
}


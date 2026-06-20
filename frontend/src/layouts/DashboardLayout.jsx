import { Outlet } from 'react-router-dom'
import { useEffect, useMemo, useState } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import AppFooter from '../components/layout/AppFooter'
import { api } from '../api/client'
import { Spinner } from '../components/ui'
import { useAppConfig } from '../context/AppConfigContext'
import { CACHE_KEYS, readSessionCache, writeSessionCache } from '../lib/sessionCache'

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(true)
  const cachedCollections = useMemo(() => readSessionCache(CACHE_KEYS.collections, 30 * 60 * 1000), [])
  const [collections, setCollections] = useState(cachedCollections || [])
  const [loading, setLoading] = useState(!cachedCollections?.length)
  const { subtitle, iconUrl } = useAppConfig()

  useEffect(() => {
    let cancelled = false
    api
      .collections()
      .then((d) => {
        if (cancelled) return
        const items = d.collections || []
        setCollections(items)
        writeSessionCache(CACHE_KEYS.collections, items)
      })
      .catch(() => {
        if (!cancelled && !cachedCollections?.length) setCollections([])
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [cachedCollections?.length])

  if (loading && !collections.length) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F8FAFC]">
        <Spinner size="lg" />
      </div>
    )
  }

  return (
    <div className="app-shell">
      <Sidebar
        collections={collections}
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        appSubtitle={subtitle || 'Analítica criminal institucional'}
        appIconUrl={iconUrl}
      />
      <div className="main-column">
        <Header />
        <main className="main-content animate-fade-up" id="main-content">
          <Outlet context={{ collections }} />
          <AppFooter />
        </main>
      </div>
    </div>
  )
}

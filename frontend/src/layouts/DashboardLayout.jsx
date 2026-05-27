import { Outlet } from 'react-router-dom'
import { useEffect, useState } from 'react'
import Sidebar from '../components/Sidebar'
import Header from '../components/Header'
import { api } from '../api/client'
import { Spinner } from '../components/ui'
import { useAppConfig } from '../context/AppConfigContext'

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [collections, setCollections] = useState([])
  const [loading, setLoading] = useState(true)
  const { appName, subtitle, iconUrl } = useAppConfig()

  useEffect(() => {
    api
      .collections()
      .then((d) => setCollections(d.collections || []))
      .catch(() => setCollections([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50">
        <Spinner />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar
        collections={collections}
        collapsed={collapsed}
        onToggle={() => setCollapsed((c) => !c)}
        appName={appName}
        appSubtitle={subtitle}
        appIconUrl={iconUrl}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header
          title={appName}
          subtitle={subtitle}
        />
        <main className="flex-1 overflow-auto p-6" id="main-content">
          <Outlet context={{ collections }} />
        </main>
      </div>
    </div>
  )
}


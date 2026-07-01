import { useEffect, useRef, useState } from 'react'
import { cn } from '../lib/cn'
import { api } from '../api/client'
import { adminApi } from '../api/admin'

export function userInitials(user) {
  if (!user) return 'CT'
  const a = String(user.nombres || '').trim().charAt(0)
  const b = String(user.apellidos || '').trim().charAt(0)
  return (a + b).toUpperCase() || 'CT'
}

export function userPhotoVersion(user) {
  if (!user?.tiene_foto) return ''
  return String(user.foto_actualizada_en || user.actualizado_en || '')
}

function withCacheBust(path, version) {
  if (!version) return path
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}v=${encodeURIComponent(version)}`
}

async function fetchUserPhotoBlob(userId, { selfFallback = false, version = '' } = {}) {
  try {
    return await adminApi.userFotoBlob(userId, version)
  } catch (adminErr) {
    if (!selfFallback) throw adminErr
    return api.authProfileFotoBlob(version)
  }
}

export default function UserAvatar({
  user,
  className,
  textClassName,
  adminPhoto = false,
  photoUrl: externalPhotoUrl,
  selfFallback = false,
  managedPhoto = false,
  photoVersion,
}) {
  const [fotoUrl, setFotoUrl] = useState(externalPhotoUrl || null)
  const objUrlRef = useRef(null)
  const userId = user?.id_usuario
  const tieneFoto = Boolean(user?.tiene_foto)
  const version = photoVersion ?? userPhotoVersion(user)

  useEffect(() => {
    if (managedPhoto) {
      setFotoUrl(externalPhotoUrl || null)
      return undefined
    }

    if (externalPhotoUrl) {
      setFotoUrl(externalPhotoUrl)
      return undefined
    }

    let cancelled = false

    const load = async () => {
      if (!userId) {
        setFotoUrl(null)
        return
      }
      if (!adminPhoto && !tieneFoto) {
        setFotoUrl(null)
        return
      }
      try {
        const { blob } = adminPhoto
          ? await fetchUserPhotoBlob(userId, { selfFallback, version })
          : await api.authProfileFotoBlob(version)
        if (cancelled) return
        if (objUrlRef.current) URL.revokeObjectURL(objUrlRef.current)
        const url = URL.createObjectURL(blob)
        objUrlRef.current = url
        setFotoUrl(url)
      } catch {
        if (!cancelled) setFotoUrl(null)
      }
    }

    load()
    return () => {
      cancelled = true
      if (objUrlRef.current) {
        URL.revokeObjectURL(objUrlRef.current)
        objUrlRef.current = null
      }
    }
  }, [
    userId,
    tieneFoto,
    adminPhoto,
    externalPhotoUrl,
    selfFallback,
    managedPhoto,
    version,
  ])

  const initials = userInitials(user)

  if (fotoUrl) {
    return (
      <img
        src={fotoUrl}
        alt={initials}
        className={cn('h-full w-full object-cover', className)}
      />
    )
  }

  return (
    <span className={cn('font-bold text-white', textClassName)}>{initials}</span>
  )
}

export function useAdminUserPhotoUrls(users, currentUserId, reloadKey = 0) {
  const [photoUrls, setPhotoUrls] = useState({})

  const usersSignature = (users || [])
    .map((u) => `${u.id_usuario}:${u.tiene_foto ? 1 : 0}:${userPhotoVersion(u)}`)
    .join('|')

  useEffect(() => {
    let cancelled = false
    const created = []

    async function loadAll() {
      const next = {}
      await Promise.all(
        (users || []).map(async (u) => {
          const uid = Number(u.id_usuario)
          if (!uid) return
          const isSelf = Number(currentUserId) === uid
          if (!u.tiene_foto && !isSelf) return
          try {
            const version = userPhotoVersion(u) || String(reloadKey)
            const { blob } = await fetchUserPhotoBlob(uid, {
              selfFallback: isSelf,
              version,
            })
            if (cancelled) return
            const url = URL.createObjectURL(blob)
            created.push(url)
            next[uid] = url
          } catch {
            /* sin foto */
          }
        })
      )
      if (!cancelled) setPhotoUrls(next)
    }

    if (users?.length) {
      loadAll()
    } else {
      setPhotoUrls({})
    }

    return () => {
      cancelled = true
      created.forEach((url) => URL.revokeObjectURL(url))
    }
  }, [usersSignature, currentUserId, reloadKey])

  return photoUrls
}

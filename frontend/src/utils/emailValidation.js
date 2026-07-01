const EMAIL_FORMAT_RE =
  /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/

const KNOWN_EMAIL_DOMAINS = new Set([
  'gmail.com',
  'googlemail.com',
  'hotmail.com',
  'hotmail.es',
  'outlook.com',
  'outlook.es',
  'live.com',
  'msn.com',
  'yahoo.com',
  'yahoo.es',
  'ymail.com',
  'icloud.com',
  'me.com',
  'mac.com',
  'protonmail.com',
  'proton.me',
  'pm.me',
  'aol.com',
  'mail.com',
  'zoho.com',
  'gmx.com',
  'gmx.es',
  'gmx.net',
  'yandex.com',
  'yandex.ru',
  'tutanota.com',
  'tuta.io',
  'fastmail.com',
  'hey.com',
  'mail.ru',
  'inbox.ru',
  'list.ru',
  'bk.ru',
  'orange.fr',
  'orange.es',
  'libero.it',
  'web.de',
  't-online.de',
  'qq.com',
  '163.com',
  '126.com',
  'sina.com',
  'rediffmail.com',
])

export function validateEmailAddress(email) {
  const normalized = String(email || '')
    .trim()
    .toLowerCase()
  if (!normalized) {
    return { ok: false, message: 'El correo electrónico es obligatorio' }
  }
  if (!EMAIL_FORMAT_RE.test(normalized)) {
    return {
      ok: false,
      message:
        'Formato inválido. Usa un dominio real, por ejemplo usuario@gmail.com o usuario@empresa.com',
    }
  }

  const [, domain] = normalized.split('@')
  const tld = domain.split('.').pop() || ''
  if (tld.length < 2 || !/^[a-z]+$/.test(tld)) {
    return {
      ok: false,
      message: 'Dominio inválido. Ejemplos: gmail.com, hotmail.com, outlook.com',
    }
  }

  if (KNOWN_EMAIL_DOMAINS.has(domain)) {
    return { ok: true, email: normalized }
  }

  if (import.meta.env.DEV && domain.endsWith('crimetrack.local')) {
    return { ok: true, email: normalized }
  }

  return {
    ok: true,
    email: normalized,
    needsServerCheck: true,
  }
}

export const EMAIL_HINT =
  'Usa un correo con dominio válido (gmail.com, hotmail.com, outlook.com, etc.)'

import { api } from './client'

const B = '/packages/involucrados'

export const involucradosApi = {
  buscar: (q, limit = 20) =>
    api.request(`${B}/buscar/?q=${encodeURIComponent(q || '')}&limit=${limit}`),
  perfil: (idInvolucrado) => api.request(`${B}/${idInvolucrado}/perfil/`),
  actualizar: (idInvolucrado, body) =>
    api.request(`${B}/${idInvolucrado}/`, {
      method: 'PATCH',
      body: JSON.stringify(body),
    }),
  subirFoto: (idInvolucrado, formData) =>
    api.uploadForm(`${B}/${idInvolucrado}/foto/`, formData),
  fotoBlob: (idInvolucrado) => api.fetchBlob(`${B}/${idInvolucrado}/foto/`),
}

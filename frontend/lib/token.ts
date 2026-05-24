'use client'

export const getToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem('notion_token') : null

export const getDatabaseId = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem('notion_database_id') : null

export const saveCredentials = (token: string, databaseId: string) => {
  localStorage.setItem('notion_token', token)
  localStorage.setItem('notion_database_id', databaseId)
}

export const clearCredentials = () => {
  localStorage.removeItem('notion_token')
  localStorage.removeItem('notion_database_id')
}

export interface SearchPreset {
  name: string
  keyword: string
  location: string
  country: string
  count: string
}

export interface LastSearch {
  keyword: string
  location: string
  country: string
  count: string
}

export const saveLastSearch = (s: LastSearch): void => {
  if (typeof window !== 'undefined')
    localStorage.setItem('last_search', JSON.stringify(s))
}

export const getLastSearch = (): LastSearch | null => {
  if (typeof window === 'undefined') return null
  try { return JSON.parse(localStorage.getItem('last_search') ?? 'null') } catch { return null }
}

export const getPresets = (): SearchPreset[] => {
  if (typeof window === 'undefined') return []
  try { return JSON.parse(localStorage.getItem('search_presets') ?? '[]') } catch { return [] }
}

export const savePreset = (p: SearchPreset): void => {
  const updated = getPresets().filter(x => x.name !== p.name)
  localStorage.setItem('search_presets', JSON.stringify([...updated, p]))
}

export const deletePreset = (name: string): void => {
  localStorage.setItem('search_presets', JSON.stringify(getPresets().filter(p => p.name !== name)))
}

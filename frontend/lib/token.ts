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

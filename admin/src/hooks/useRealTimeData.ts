'use client'

import { useEffect, useState, useCallback } from 'react'

export function useRealTimeData<T>(
  url: string,
  initialData: T,
  interval: number = 3000 // 3 seconds default
) {
  const [data, setData] = useState<T>(initialData)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      const response = await fetch(url, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        },
      })

      if (!response.ok) {
        throw new Error(`Failed to fetch: ${response.statusText}`)
      }

      const newData = await response.json()
      setData(newData)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error'
      setError(message)
      console.error('Real-time data fetch error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [url])

  // Initial fetch on mount
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Poll data at specified interval
  useEffect(() => {
    const intervalId = setInterval(() => {
      fetchData()
    }, interval)

    return () => clearInterval(intervalId)
  }, [fetchData, interval])

  return { data, isLoading, error, refetch: fetchData }
}

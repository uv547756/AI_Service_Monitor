import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for polling an async data-fetching function.
 * @param {Function} fetchFn — async function that returns data
 * @param {number} interval — polling interval in ms (default 5000)
 * @param {Array} deps — dependency array to trigger immediate refetch
 */
export function usePolling(fetchFn, interval = 5000, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  const load = useCallback(async () => {
    try {
      const result = await fetchFn();
      setData(result);
      setError(null);
    } catch (err) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [fetchFn]);

  useEffect(() => {
    load();
    intervalRef.current = setInterval(load, interval);
    return () => clearInterval(intervalRef.current);
  }, [load, interval, ...deps]);

  return { data, loading, error, refetch: load };
}

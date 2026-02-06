import { useState, useCallback } from 'react';
import { AxiosError } from 'axios';

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

interface UseApiReturn<T, P extends any[]> extends UseApiState<T> {
  execute: (...params: P) => Promise<T | null>;
  reset: () => void;
}

/**
 * Custom hook for API calls with loading and error states
 * @param apiFunction - The API function to call
 */
export function useApi<T, P extends any[]>(
  apiFunction: (...params: P) => Promise<{ data: T }>
): UseApiReturn<T, P> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(
    async (...params: P): Promise<T | null> => {
      setState({ data: null, loading: true, error: null });
      
      try {
        const response = await apiFunction(...params);
        setState({ data: response.data, loading: false, error: null });
        return response.data;
      } catch (err) {
        const error = err as AxiosError<{ detail?: string }>;
        const errorMessage = 
          error.response?.data?.detail || 
          error.message || 
          'An unexpected error occurred';
        
        setState({ data: null, loading: false, error: errorMessage });
        return null;
      }
    },
    [apiFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null });
  }, []);

  return {
    ...state,
    execute,
    reset,
  };
}

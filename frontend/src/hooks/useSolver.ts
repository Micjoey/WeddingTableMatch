import { useCallback } from 'react';
import { useAppStore } from '../store';

// Hook for solver API interactions
export const useSolver = () => {
  const solve = useAppStore((s) => s.solve);
  const updateScores = useAppStore((s) => s.updateScores);
  const isLoading = useAppStore((s) => s.isLoading);
  const error = useAppStore((s) => s.error);

  const handleSolve = useCallback(async () => {
    await solve();
  }, [solve]);

  const handleScoreUpdate = useCallback(async () => {
    await updateScores();
  }, [updateScores]);

  return {
    solve: handleSolve,
    updateScores: handleScoreUpdate,
    isLoading,
    error,
  };
};

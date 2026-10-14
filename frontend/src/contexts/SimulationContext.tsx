import React, { createContext, useContext, useState, useCallback } from 'react';
import type { SimulationOverlay } from '../types';

interface SimulationContextValue {
  simulationOverlay: SimulationOverlay | null;
  setSimulationOverlay: (o: SimulationOverlay | null) => void;
  clearOverlay: () => void;
  selectedComponentId: string | null;
  setSelectedComponentId: (id: string | null) => void;
  highlightedPathIds: string[];
  setHighlightedPathIds: (ids: string[]) => void;
}

const SimulationContext = createContext<SimulationContextValue | null>(null);

export function SimulationProvider({ children }: { children: React.ReactNode }) {
  const [simulationOverlay, setSimulationOverlayState] = useState<SimulationOverlay | null>(null);
  const [selectedComponentId, setSelectedComponentId] = useState<string | null>(null);
  const [highlightedPathIds, setHighlightedPathIds] = useState<string[]>([]);
  const setSimulationOverlay = useCallback((o: SimulationOverlay | null) => setSimulationOverlayState(o), []);
  const clearOverlay = useCallback(() => {
    setSimulationOverlayState(null);
    setHighlightedPathIds([]);
  }, []);
  return (
    <SimulationContext.Provider value={{ simulationOverlay, setSimulationOverlay, clearOverlay, selectedComponentId, setSelectedComponentId, highlightedPathIds, setHighlightedPathIds }}>
      {children}
    </SimulationContext.Provider>
  );
}

export function useSimulation(): SimulationContextValue {
  const ctx = useContext(SimulationContext);
  if (!ctx) throw new Error('useSimulation must be within SimulationProvider');
  return ctx;
}

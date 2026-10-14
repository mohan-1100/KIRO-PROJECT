import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Scenario } from '../types';
import { listScenarios } from '../api/scenarios';

interface ScenarioContextValue {
  scenarios: Scenario[];
  activeScenarioId: string | null;
  activeScenario: Scenario | null;
  setActiveScenarioId: (id: string) => void;
  refreshScenarios: () => Promise<void>;
  loading: boolean;
  error: string | null;
}

const ScenarioContext = createContext<ScenarioContextValue | null>(null);

export function ScenarioProvider({ children }: { children: React.ReactNode }) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [activeScenarioId, setActiveScenarioIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshScenarios = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listScenarios();
      setScenarios(data);
      if (data.length > 0 && !activeScenarioId) {
        setActiveScenarioIdState(data[0].id);
      }
    } catch {
      setError('Failed to load scenarios');
    } finally {
      setLoading(false);
    }
  }, [activeScenarioId]);

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { refreshScenarios(); }, []);

  const setActiveScenarioId = useCallback((id: string) => setActiveScenarioIdState(id), []);
  const activeScenario = scenarios.find(s => s.id === activeScenarioId) ?? null;

  return (
    <ScenarioContext.Provider value={{ scenarios, activeScenarioId, activeScenario, setActiveScenarioId, refreshScenarios, loading, error }}>
      {children}
    </ScenarioContext.Provider>
  );
}

export function useScenario(): ScenarioContextValue {
  const ctx = useContext(ScenarioContext);
  if (!ctx) throw new Error('useScenario must be within ScenarioProvider');
  return ctx;
}

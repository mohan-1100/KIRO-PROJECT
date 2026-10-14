import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { SimulationProvider, useSimulation } from '../contexts/SimulationContext';
import type { SimulationOverlay } from '../types';

const mockOverlay: SimulationOverlay = {
  simId: 'sim-1', failedTargetId: 'comp-1',
  failedTargetType: 'component', failureType: 'component_unavailable',
  affectedComponentIds: ['comp-2'], possibleAltComponentIds: [],
  impactReport: {} as any,
};

describe('SimulationContext clearOverlay', () => {
  it('clears simulationOverlay when clearOverlay is called', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => <SimulationProvider>{children}</SimulationProvider>;
    const { result } = renderHook(() => useSimulation(), { wrapper });
    act(() => { result.current.setSimulationOverlay(mockOverlay); });
    expect(result.current.simulationOverlay).not.toBeNull();
    act(() => { result.current.clearOverlay(); });
    expect(result.current.simulationOverlay).toBeNull();
  });

  it('clears highlightedPathIds when clearOverlay is called', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => <SimulationProvider>{children}</SimulationProvider>;
    const { result } = renderHook(() => useSimulation(), { wrapper });
    act(() => {
      result.current.setSimulationOverlay(mockOverlay);
      result.current.setHighlightedPathIds(['comp-1', 'comp-2']);
    });
    act(() => { result.current.clearOverlay(); });
    expect(result.current.highlightedPathIds).toEqual([]);
  });
});

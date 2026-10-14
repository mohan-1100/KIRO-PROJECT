import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { SimulationProvider, useSimulation } from '../contexts/SimulationContext';

describe('DetailsPanel via SimulationContext', () => {
  it('tracks selectedComponentId correctly', () => {
    const wrapper = ({ children }: { children: React.ReactNode }) => <SimulationProvider>{children}</SimulationProvider>;
    const { result } = renderHook(() => useSimulation(), { wrapper });
    expect(result.current.selectedComponentId).toBeNull();
    act(() => { result.current.setSelectedComponentId('comp-abc'); });
    expect(result.current.selectedComponentId).toBe('comp-abc');
    act(() => { result.current.setSelectedComponentId(null); });
    expect(result.current.selectedComponentId).toBeNull();
  });
});

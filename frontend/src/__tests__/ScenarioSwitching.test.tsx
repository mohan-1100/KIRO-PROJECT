import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { ScenarioProvider, useScenario } from '../contexts/ScenarioContext';

const MOCK_SCENARIOS = [
  { id: 'sc-1', name: 'Database Failure', description: null, created_at: '2024-01-01T00:00:00Z' },
  { id: 'sc-2', name: 'Shared Failure', description: null, created_at: '2024-01-01T00:01:00Z' },
];

describe('ScenarioContext', () => {
  it('auto-selects the first scenario on load', async () => {
    global.fetch = async () => new Response(JSON.stringify(MOCK_SCENARIOS), { status: 200 }) as any;
    const wrapper = ({ children }: { children: React.ReactNode }) => <ScenarioProvider>{children}</ScenarioProvider>;
    const { result } = renderHook(() => useScenario(), { wrapper });
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.activeScenarioId).toBe('sc-1');
    expect(result.current.activeScenario?.name).toBe('Database Failure');
  });

  it('clears overlay when scenario changes (ScenarioSwitching)', async () => {
    // Switching scenario is done via setActiveScenarioId — overlay is cleared by the caller (TopBar)
    // This test verifies setActiveScenarioId updates activeScenarioId correctly
    global.fetch = async () => new Response(JSON.stringify(MOCK_SCENARIOS), { status: 200 }) as any;
    const wrapper = ({ children }: { children: React.ReactNode }) => <ScenarioProvider>{children}</ScenarioProvider>;
    const { result } = renderHook(() => useScenario(), { wrapper });
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.activeScenarioId).toBe('sc-1');
    const { act } = await import('@testing-library/react');
    await act(async () => { result.current.setActiveScenarioId('sc-2'); });
    expect(result.current.activeScenarioId).toBe('sc-2');
  });
});

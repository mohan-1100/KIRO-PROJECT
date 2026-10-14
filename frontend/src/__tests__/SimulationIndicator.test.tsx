import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { SimulationProvider, useSimulation } from '../contexts/SimulationContext';
import { TopBar } from '../components/layout/TopBar';
import { ScenarioProvider } from '../contexts/ScenarioContext';
import { BrowserRouter } from 'react-router-dom';

// Mock fetch so listScenarios doesn't fail
global.fetch = async () => new Response(JSON.stringify([]), { status: 200 }) as any;

describe('SimulationActiveIndicator', () => {
  it('is hidden when no simulation is active', () => {
    render(
      <BrowserRouter>
        <ScenarioProvider>
          <SimulationProvider>
            <TopBar />
          </SimulationProvider>
        </ScenarioProvider>
      </BrowserRouter>
    );
    const indicator = document.querySelector('[data-testid="simulation-active-indicator"]');
    expect(indicator).toBeNull();
  });
});

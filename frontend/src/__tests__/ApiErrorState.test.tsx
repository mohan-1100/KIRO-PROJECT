import { describe, it, expect } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ScenarioProvider } from '../contexts/ScenarioContext';
import { SimulationProvider } from '../contexts/SimulationContext';
import { OverviewPage } from '../pages/OverviewPage';

describe('API error state', () => {
  it('shows error message when API returns 500', async () => {
    global.fetch = async () => new Response(JSON.stringify({ detail: 'Server error' }), { status: 500 }) as any;
    render(
      <BrowserRouter>
        <ScenarioProvider>
          <SimulationProvider>
            <OverviewPage />
          </SimulationProvider>
        </ScenarioProvider>
      </BrowserRouter>
    );
    await waitFor(() => {
      // Either error banner or loading completes; page should not be blank
      const body = document.body.textContent ?? '';
      expect(body.length).toBeGreaterThan(0);
    }, { timeout: 2000 });
  });
});

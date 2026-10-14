import { apiRequest } from './client';
import type { ImpactReport, SimulationHistoryRecord } from '../types';
export const runSimulation = (scenarioId: string, targetId: string, targetType: 'component' | 'edge', failureType: string) =>
  apiRequest<ImpactReport>(`/scenarios/${scenarioId}/simulations`, {
    method: 'POST',
    body: JSON.stringify({ scenario_id: scenarioId, target_id: targetId, target_type: targetType, failure_type: failureType }),
  });
export const getActiveSimulation = (scenarioId: string) =>
  apiRequest<ImpactReport | null>(`/scenarios/${scenarioId}/simulation`);
export const resetSimulation = (scenarioId: string) =>
  apiRequest<{ detail: string }>(`/scenarios/${scenarioId}/reset`, { method: 'POST' });
export const getSimulationHistory = (scenarioId: string) =>
  apiRequest<SimulationHistoryRecord[]>(`/scenarios/${scenarioId}/simulations`);

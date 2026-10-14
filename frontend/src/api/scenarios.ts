import { apiRequest } from './client';
import type { Scenario } from '../types';
export const listScenarios = () => apiRequest<Scenario[]>('/scenarios');
export const createScenario = (name: string, description?: string) =>
  apiRequest<Scenario>('/scenarios', { method: 'POST', body: JSON.stringify({ name, description }) });
export const deleteScenario = (id: string) =>
  apiRequest<{ detail: string }>(`/scenarios/${id}`, { method: 'DELETE' });

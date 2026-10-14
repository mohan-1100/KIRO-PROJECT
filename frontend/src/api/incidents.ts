import { apiRequest } from './client';
import type { SimulationHistoryRecord } from '../types';
export const listIncidents = () => apiRequest<SimulationHistoryRecord[]>('/incidents');
export const resolveIncident = (id: string) => apiRequest<SimulationHistoryRecord>(`/incidents/${id}`, {
  method: 'PATCH', body: JSON.stringify({ status: 'resolved' }),
});

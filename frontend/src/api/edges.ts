import { apiRequest } from './client';
import type { Edge } from '../types';
type EI = { source_component_id: string; target_component_id: string; label?: string; evidence_source?: string; confirmation_status?: string; };
export const listEdges = (s: string) => apiRequest<Edge[]>(`/scenarios/${s}/edges`);
export const createEdge = (s: string, d: EI) => apiRequest<Edge>(`/scenarios/${s}/edges`, { method: 'POST', body: JSON.stringify(d) });
export const updateEdge = (s: string, e: string, d: Partial<EI>) => apiRequest<Edge>(`/scenarios/${s}/edges/${e}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteEdge = (s: string, e: string) => apiRequest<{ detail: string }>(`/scenarios/${s}/edges/${e}`, { method: 'DELETE' });

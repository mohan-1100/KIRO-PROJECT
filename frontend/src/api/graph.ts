import { apiRequest } from './client';
import type { Graph, DataQuality } from '../types';
export const getGraph = (scenarioId: string) =>
  apiRequest<Graph>(`/scenarios/${scenarioId}/graph`);
export const getDataQuality = (scenarioId: string) =>
  apiRequest<DataQuality>(`/scenarios/${scenarioId}/data-quality`);

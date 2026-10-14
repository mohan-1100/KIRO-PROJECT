import { apiRequest } from './client';
import type { Component } from '../types';
type CI = { name: string; type: string; criticality: string; health_status?: string; evidence_source?: string; confirmation_status?: string; data_quality_score?: number; };
export const listComponents = (s: string) => apiRequest<Component[]>(`/scenarios/${s}/components`);
export const getComponent = (s: string, c: string) => apiRequest<Component>(`/scenarios/${s}/components/${c}`);
export const createComponent = (s: string, d: CI) => apiRequest<Component>(`/scenarios/${s}/components`, { method: 'POST', body: JSON.stringify(d) });
export const updateComponent = (s: string, c: string, d: Partial<CI>) => apiRequest<Component>(`/scenarios/${s}/components/${c}`, { method: 'PUT', body: JSON.stringify(d) });
export const deleteComponent = (s: string, c: string) => apiRequest<{ detail: string }>(`/scenarios/${s}/components/${c}`, { method: 'DELETE' });

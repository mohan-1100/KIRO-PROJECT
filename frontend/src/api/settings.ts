import { apiRequest } from './client';
import type { Settings } from '../types';
export const getSettings = () => apiRequest<Settings>('/settings');
export const updateSettings = (hours: number) => apiRequest<Settings>('/settings', {
  method: 'PUT', body: JSON.stringify({ freshness_threshold_hours: hours }),
});

import { apiRequest } from './client';
import type { RecoveryResponse } from '../types';
export const requestRecovery = (
  scenarioId: string, simId: string,
  recoveryType: 'component' | 'edge', recoveryTargetId: string
) => apiRequest<RecoveryResponse>(`/scenarios/${scenarioId}/simulations/${simId}/recovery`, {
  method: 'POST', body: JSON.stringify({ recovery_type: recoveryType, recovery_target_id: recoveryTargetId }),
});

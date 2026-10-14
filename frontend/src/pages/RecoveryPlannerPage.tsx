import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { useSimulation } from '../contexts/SimulationContext';
import { requestRecovery } from '../api/recovery';
import { getGraph } from '../api/graph';
import type { RecoveryOption, Component } from '../types';
import { RefreshCw } from 'lucide-react';

export function RecoveryPlannerPage() {
  const { activeScenarioId } = useScenario();
  const { simulationOverlay } = useSimulation();
  const [options, setOptions] = useState<RecoveryOption[]>([]);
  const [components, setComponents] = useState<Component[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!activeScenarioId) return;
    getGraph(activeScenarioId).then(g => setComponents(g.components)).catch(() => {});
  }, [activeScenarioId]);

  const getComponentName = (id: string) =>
    components.find(c => c.id === id)?.name ?? id.slice(0, 8) + '…';

  const fetchOptions = async () => {
    if (!activeScenarioId || !simulationOverlay) return;
    setLoading(true); setError(null);
    try {
      const recoveryType = simulationOverlay.failedTargetType;
      const result = await requestRecovery(activeScenarioId, simulationOverlay.simId, recoveryType, simulationOverlay.failedTargetId);
      setOptions(result.options);
    } catch { setError('Failed to compute recovery options'); } finally { setLoading(false); }
  };

  if (!simulationOverlay) {
    return (
      <div className="p-8 max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-slate-100 mb-4">Recovery Planner</h1>
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-8 text-center">
          <RefreshCw className="w-8 h-8 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400">No active simulation. Run a simulation to see recovery options.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Recovery Planner</h1>
        <button onClick={fetchOptions} disabled={loading} className="bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded text-sm">
          {loading ? 'Analysing…' : 'Analyse Recovery Options'}
        </button>
      </div>
      <div className="bg-amber-900/20 border border-amber-700 rounded-lg p-3 text-amber-300 text-sm">
        Simulated Projection — Recovery analysis does not account for configuration, data consistency, or routing factors.
      </div>
      {error && <div className="text-red-400 text-sm">{error}</div>}
      {options.length > 0 && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-700">
              <tr>
                {['Candidate','Recovered','Still Affected','Projected Score'].map(h => (
                  <th key={h} className="text-left text-slate-400 px-4 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {options.slice(0, 4).map((opt, i) => (
                <tr key={i} className="border-b border-slate-800">
                  <td className="px-4 py-3 text-slate-200">{getComponentName(opt.recovery_target_id)}</td>
                  <td className="px-4 py-3 text-emerald-400 font-mono">{opt.services_recovered_count}</td>
                  <td className="px-4 py-3 text-red-400 font-mono">{opt.services_still_affected_count}</td>
                  <td className="px-4 py-3 font-mono text-slate-200">{opt.projected_impact_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {options.some(o => o.no_additional_recovery) && (
            <p className="text-slate-500 text-xs px-4 py-2">Some recovery options would not reduce the affected service count further.</p>
          )}
        </div>
      )}
    </div>
  );
}

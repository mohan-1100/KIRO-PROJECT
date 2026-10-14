import { Activity, ChevronDown, Zap } from 'lucide-react';
import { useScenario } from '../../contexts/ScenarioContext';
import { useSimulation } from '../../contexts/SimulationContext';
import { getActiveSimulation } from '../../api/simulations';
import type { ImpactReport } from '../../types';

export function TopBar() {
  const { scenarios, activeScenarioId, setActiveScenarioId } = useScenario();
  const { simulationOverlay, setSimulationOverlay, clearOverlay } = useSimulation();

  const handleScenarioChange = async (newId: string) => {
    clearOverlay();
    setActiveScenarioId(newId);
    try {
      const existing = await getActiveSimulation(newId);
      if (existing) {
        const r = existing as ImpactReport;
        setSimulationOverlay({
          simId: r.sim_id, failedTargetId: r.failed_target_id,
          failedTargetType: r.failed_target_type, failureType: r.failure_type,
          affectedComponentIds: [...r.directly_affected.map(c => c.component_id), ...r.transitively_affected.map(c => c.component_id)],
          possibleAltComponentIds: r.possible_alt_path_components.map(c => c.component_id),
          impactReport: r,
        });
      }
    } catch { /* 204 = no active sim */ }
  };

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-700 flex items-center px-4 gap-4 shrink-0 z-10">
      <div className="flex items-center gap-2 text-blue-400 font-bold text-lg min-w-[140px]">
        <Activity className="w-5 h-5" />
        <span>ImpactLens</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-slate-400 text-sm">Scenario:</span>
        <div className="relative">
          <select
            className="bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-1.5 pr-8 appearance-none cursor-pointer hover:border-slate-500 focus:outline-none focus:border-blue-500"
            value={activeScenarioId ?? ''}
            onChange={e => handleScenarioChange(e.target.value)}
            aria-label="Select scenario"
          >
            {scenarios.length === 0 && <option value="">No Scenarios Available</option>}
            {scenarios.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select>
          <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      </div>
      <span className="text-xs bg-amber-900/50 text-amber-400 border border-amber-700 px-2 py-0.5 rounded">Simulated Demo</span>
      {simulationOverlay && (
        <div data-testid="simulation-active-indicator" className="flex items-center gap-2 bg-red-900/40 border border-red-700 rounded px-3 py-1 ml-auto">
          <Zap className="w-4 h-4 text-red-400 shrink-0" />
          <span className="text-red-300 text-sm font-medium">Simulation Active:</span>
          <span className="text-red-200 text-sm">
            {simulationOverlay.failedTargetType === 'edge' ? 'dependency link unavailable' : simulationOverlay.failureType.replace(/_/g,' ')}
          </span>
        </div>
      )}
    </header>
  );
}
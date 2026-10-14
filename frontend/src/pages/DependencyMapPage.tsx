import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { useSimulation } from '../contexts/SimulationContext';
import { getGraph } from '../api/graph';
import type { Graph } from '../types';
import { Network } from 'lucide-react';

export function DependencyMapPage() {
  const { activeScenarioId } = useScenario();
  const { simulationOverlay } = useSimulation();
  const [graph, setGraph] = useState<Graph | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const load = () => {
    if (!activeScenarioId) return;
    setLoading(true); setError(null);
    getGraph(activeScenarioId).then(setGraph).catch(() => setError('Failed to load graph')).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, [activeScenarioId]);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <Network className="w-6 h-6 text-blue-400" />
        <h1 className="text-2xl font-bold text-slate-100">Dependency Map</h1>
        <span className="text-slate-500 text-sm">(Interactive React Flow canvas — full implementation in progress)</span>
      </div>
      {error && <div className="bg-red-900/30 border border-red-700 rounded p-3 text-red-300 text-sm flex justify-between"><span>{error}</span><button onClick={load} className="underline">Retry</button></div>}
      {loading && <p className="text-slate-400">Loading graph…</p>}
      {graph && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
          <div className="flex gap-6 text-sm text-slate-400">
            <span>{graph.components.length} components</span>
            <span>{graph.edges.length} edges</span>
            {simulationOverlay && <span className="text-red-400">{simulationOverlay.affectedComponentIds.length} affected</span>}
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {graph.components.map(c => {
              const isAffected = simulationOverlay?.affectedComponentIds.includes(c.id);
              const isFailed = simulationOverlay?.failedTargetId === c.id;
              const hasAlt = simulationOverlay?.possibleAltComponentIds.includes(c.id);
              const border = isFailed ? 'border-red-500 bg-red-900/20'
                : isAffected ? 'border-amber-500 bg-amber-900/10'
                : hasAlt ? 'border-blue-500 bg-blue-900/10'
                : 'border-slate-700';
              return (
                <div key={c.id} className={'border rounded p-3 text-sm ' + border}>
                  <p className="font-medium text-slate-100 truncate">{c.name}</p>
                  <p className="text-slate-400 text-xs capitalize">{c.type.replace(/_/g,' ')}</p>
                  <p className="text-xs capitalize mt-1">
                    <span className={c.health_status === 'healthy' ? 'text-emerald-400' : c.health_status === 'failed' ? 'text-red-400' : 'text-amber-400'}>{c.health_status}</span>
                    {' · ' + c.criticality}
                  </p>
                  {isFailed && <p className="text-red-300 text-xs mt-1">FAILED TARGET</p>}
                  {hasAlt && !isFailed && <p className="text-blue-300 text-xs mt-1">Possible alt path</p>}
                </div>
              );
            })}
          </div>
          <p className="text-slate-500 text-xs">Edge convention: A to B means B depends on A. Affected services shown with amber border.</p>
        </div>
      )}
    </div>
  );
}

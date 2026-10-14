import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { useSimulation } from '../contexts/SimulationContext';
import { getGraph } from '../api/graph';
import { getSimulationHistory } from '../api/simulations';
import { listIncidents } from '../api/incidents';
import type { Component, SimulationHistoryRecord } from '../types';

interface Metrics {
  total: number; healthy: number; degraded: number; failed: number;
  activeIncidents: number; potentiallyAffected: number;
}

function MetricCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-slate-900 border border-slate-700 rounded-lg p-4">
      <p className="text-slate-400 text-sm mb-1">{label}</p>
      <p className={color + ' text-3xl font-bold font-mono'}>{value}</p>
    </div>
  );
}

export function OverviewPage() {
  const { activeScenarioId } = useScenario();
  const { simulationOverlay } = useSimulation();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [recentSims, setRecentSims] = useState<SimulationHistoryRecord[]>([]);
  const [topComponents, setTopComponents] = useState<Component[]>([]);
  const [completeness, setCompleteness] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeScenarioId) return;
    setLoading(true);
    setError(null);
    Promise.all([
      getGraph(activeScenarioId),
      getSimulationHistory(activeScenarioId),
      listIncidents(),
    ]).then(([graph, history, incidents]) => {
      const comps = graph.components;
      const openIncidents = incidents.filter(i => i.status === 'open').length;
      const confirmedCount = comps.filter(c => c.confirmation_status === 'confirmed').length;
      setMetrics({
        total: comps.length,
        healthy: comps.filter(c => c.health_status === 'healthy').length,
        degraded: comps.filter(c => c.health_status === 'degraded').length,
        failed: comps.filter(c => c.health_status === 'failed').length,
        activeIncidents: openIncidents,
        potentiallyAffected: simulationOverlay
          ? simulationOverlay.affectedComponentIds.length
          : 0,
      });
      setCompleteness(comps.length > 0 ? Math.round((confirmedCount / comps.length) * 100) : 0);
      const sorted = [...comps].sort((a, b) => {
        const w = { critical: 4, high: 3, medium: 2, low: 1 };
        return (w[b.criticality] ?? 0) - (w[a.criticality] ?? 0);
      });
      setTopComponents(sorted.slice(0, 5));
      setRecentSims(history.slice(0, 3));
    }).catch(() => setError('Failed to load overview data')).finally(() => setLoading(false));
  }, [activeScenarioId, simulationOverlay]);

  if (loading) return <div className="p-8 text-slate-400">Loading overview…</div>;

  return (
    <div className="p-8 space-y-6 max-w-6xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">Overview</h1>
        <p className="text-slate-400 text-sm">Infrastructure health at a glance — all data is simulated</p>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-red-300 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 text-sm underline">Retry</button>
        </div>
      )}

      {metrics && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <MetricCard label="Total Components" value={metrics.total} color="text-slate-100" />
          <MetricCard label="Healthy" value={metrics.healthy} color="text-emerald-400" />
          <MetricCard label="Degraded" value={metrics.degraded} color="text-amber-400" />
          <MetricCard label="Failed" value={metrics.failed} color="text-red-400" />
          <MetricCard label="Active Incidents" value={metrics.activeIncidents} color="text-orange-400" />
          <MetricCard label="Potentially Affected" value={metrics.potentiallyAffected} color="text-purple-400" />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">Most Critical Components</h2>
          {topComponents.length === 0 ? (
            <p className="text-slate-500 text-sm">No components loaded</p>
          ) : (
            <ul className="space-y-2">
              {topComponents.map(c => (
                <li key={c.id} className="flex items-center justify-between text-sm">
                  <span className="text-slate-200">{c.name}</span>
                  <span className="text-xs bg-slate-800 text-slate-400 px-2 py-0.5 rounded capitalize">{c.criticality}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="bg-slate-900 border border-slate-700 rounded-lg p-4">
          <h2 className="text-sm font-semibold text-slate-300 mb-3">Recent Simulations</h2>
          {recentSims.length === 0 ? (
            <p className="text-slate-500 text-sm">No simulations recorded yet</p>
          ) : (
            <ul className="space-y-2">
              {recentSims.map(s => (
                <li key={s.id} className="text-sm border-b border-slate-800 pb-2">
                  <span className="text-slate-200 block truncate">{s.failed_target_type}: {s.failed_target_id.slice(0,8)}…</span>
                  <span className="text-slate-500 text-xs">{new Date(s.timestamp).toLocaleString()}</span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="bg-slate-900 border border-slate-700 rounded-lg p-4">
        <h2 className="text-sm font-semibold text-slate-300 mb-2">Data Completeness</h2>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-slate-800 rounded-full h-3">
            <div
              className="bg-blue-500 h-3 rounded-full transition-all"
              style={{ width: completeness + '%' }}
              role="progressbar"
              aria-valuenow={completeness}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>
          <span className="text-slate-300 font-mono text-sm w-10 text-right">{completeness}%</span>
        </div>
        <p className="text-slate-500 text-xs mt-1">Percentage of components with confirmed dependency evidence</p>
      </section>
    </div>
  );
}

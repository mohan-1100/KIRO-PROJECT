import { useEffect, useState } from 'react';
import { listIncidents, resolveIncident } from '../api/incidents';
import type { SimulationHistoryRecord } from '../types';

export function IncidentAnalysisPage() {
  const [incidents, setIncidents] = useState<SimulationHistoryRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setLoading(true);
    listIncidents().then(setIncidents).catch(() => setError('Failed to load incidents')).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleResolve = async (id: string) => {
    await resolveIncident(id).catch(() => {});
    load();
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-slate-100">Incident Analysis</h1>
      {error && <div className="bg-red-900/30 border border-red-700 rounded p-3 text-red-300 text-sm flex justify-between"><span>{error}</span><button onClick={load} className="underline">Retry</button></div>}
      {loading ? <p className="text-slate-400">Loading…</p> : incidents.length === 0 ? (
        <p className="text-slate-500">No incidents recorded yet. Run a simulation to create incidents.</p>
      ) : (
        <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-700">
              <tr>
                {['Target','Failure Type','Timestamp','Affected','Score','Status','Action'].map(h => (
                  <th key={h} className="text-left text-slate-400 px-4 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {incidents.map(i => (
                <tr key={i.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                  <td className="px-4 py-3 text-slate-200 font-mono text-xs">{i.failed_target_id.slice(0,12)}…</td>
                  <td className="px-4 py-3 text-slate-300 capitalize">{i.failure_type.replace(/_/g,' ')}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{new Date(i.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-300">{i.directly_affected_count + i.transitively_affected_count}</td>
                  <td className="px-4 py-3 font-mono text-red-400">{i.impact_score}</td>
                  <td className="px-4 py-3">
                    <span className={(i.status === 'open' ? 'bg-red-900/40 text-red-300 border-red-700' : 'bg-emerald-900/40 text-emerald-300 border-emerald-700') + ' border text-xs px-2 py-0.5 rounded capitalize'}>{i.status}</span>
                  </td>
                  <td className="px-4 py-3">
                    {i.status === 'open' && (
                      <button onClick={() => handleResolve(i.id)} className="text-xs text-blue-400 hover:text-blue-200 underline">Resolve</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

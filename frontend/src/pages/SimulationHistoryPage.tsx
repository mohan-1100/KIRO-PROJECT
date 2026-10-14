import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { getSimulationHistory } from '../api/simulations';
import type { SimulationHistoryRecord } from '../types';

export function SimulationHistoryPage() {
  const { activeScenarioId } = useScenario();
  const [records, setRecords] = useState<SimulationHistoryRecord[]>([]);
  const [selected, setSelected] = useState<SimulationHistoryRecord | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!activeScenarioId) return;
    setLoading(true);
    getSimulationHistory(activeScenarioId).then(setRecords).catch(() => {}).finally(() => setLoading(false));
  }, [activeScenarioId]);

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-slate-100">Simulation History</h1>
      {loading && <p className="text-slate-400">Loading…</p>}
      {records.length === 0 && !loading && <p className="text-slate-500">No simulations recorded for this scenario.</p>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
          <table className="w-full text-sm">
            <thead className="border-b border-slate-700">
              <tr>
                {['ID','Failure Type','Timestamp','Affected','Score'].map(h => (
                  <th key={h} className="text-left text-slate-400 px-4 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {records.map(r => (
                <tr key={r.id} onClick={() => setSelected(r)} className={(selected?.id === r.id ? 'bg-blue-900/20' : '') + ' border-b border-slate-800 hover:bg-slate-800/50 cursor-pointer'}>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">{r.id.slice(0,8)}…</td>
                  <td className="px-4 py-3 text-slate-300 capitalize">{r.failure_type.replace(/_/g,' ')}</td>
                  <td className="px-4 py-3 text-slate-400 text-xs">{new Date(r.timestamp).toLocaleString()}</td>
                  <td className="px-4 py-3 text-slate-300">{r.directly_affected_count + r.transitively_affected_count}</td>
                  <td className="px-4 py-3 font-mono text-red-400">{r.impact_score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {selected && (
          <div className="bg-slate-900 border border-slate-700 rounded-lg p-4 space-y-3">
            <h2 className="text-slate-100 font-semibold text-sm">Simulation Details</h2>
            <dl className="space-y-2 text-sm">
              <div><dt className="text-slate-500 text-xs">ID</dt><dd className="text-slate-300 font-mono text-xs">{selected.id}</dd></div>
              <div><dt className="text-slate-500 text-xs">Failure type</dt><dd className="text-slate-300 capitalize">{selected.failure_type.replace(/_/g,' ')}</dd></div>
              <div><dt className="text-slate-500 text-xs">Impact score</dt><dd className="text-red-400 font-mono font-bold text-lg">{selected.impact_score}</dd></div>
              <div><dt className="text-slate-500 text-xs">Data confidence</dt><dd className="text-blue-400 font-mono">{selected.data_confidence_score}</dd></div>
              <div><dt className="text-slate-500 text-xs">Status</dt><dd className="capitalize text-slate-300">{selected.status}</dd></div>
            </dl>
          </div>
        )}
      </div>
    </div>
  );
}

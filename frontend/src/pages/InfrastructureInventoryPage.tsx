import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { listComponents, updateComponent } from '../api/components';
import type { Component } from '../types';

export function InfrastructureInventoryPage() {
  const { activeScenarioId } = useScenario();
  const [components, setComponents] = useState<Component[]>([]);
  const [filter, setFilter] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editDQ, setEditDQ] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!activeScenarioId) return;
    listComponents(activeScenarioId).then(setComponents).catch(() => setError('Failed to load components'));
  };

  useEffect(() => { load(); }, [activeScenarioId]);

  const filtered = components.filter(c => c.name.toLowerCase().includes(filter.toLowerCase()));

  const startEdit = (c: Component) => { setEditingId(c.id); setEditDQ(String(c.data_quality_score)); };

  const saveEdit = async (c: Component) => {
    if (!activeScenarioId) return;
    const dq = parseInt(editDQ, 10);
    if (isNaN(dq) || dq < 0 || dq > 100) { setError('DQ score must be 0–100'); return; }
    try {
      await updateComponent(activeScenarioId, c.id, { data_quality_score: dq });
      load();
      setEditingId(null);
    } catch { setError('Failed to save'); }
  };

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-4">
      <h1 className="text-2xl font-bold text-slate-100">Infrastructure Inventory</h1>
      <input value={filter} onChange={e => setFilter(e.target.value)} placeholder="Filter by name…" className="w-64 bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-2" />
      {error && <div className="text-red-400 text-sm">{error}</div>}
      <div className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-700">
            <tr>
              {['Name','Type','Status','Criticality','Confirmation','DQ Score','Actions'].map(h => (
                <th key={h} className="text-left text-slate-400 px-4 py-3 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filtered.map(c => (
              <tr key={c.id} className="border-b border-slate-800 hover:bg-slate-800/50">
                <td className="px-4 py-3 text-slate-200 font-medium">{c.name}</td>
                <td className="px-4 py-3 text-slate-400 capitalize">{c.type.replace(/_/g,' ')}</td>
                <td className="px-4 py-3 capitalize text-slate-300">{c.health_status}</td>
                <td className="px-4 py-3 capitalize text-slate-300">{c.criticality}</td>
                <td className="px-4 py-3 capitalize text-slate-300">{c.confirmation_status}</td>
                <td className="px-4 py-3">
                  {editingId === c.id ? (
                    <input type="number" min={0} max={100} value={editDQ} onChange={e => setEditDQ(e.target.value)} className="w-16 bg-slate-700 border border-slate-500 text-slate-100 text-sm rounded px-2 py-0.5" />
                  ) : (
                    <span className={(c.data_quality_score < 50 ? 'text-amber-400' : 'text-emerald-400') + ' font-mono'}>{c.data_quality_score}</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {editingId === c.id ? (
                    <div className="flex gap-2">
                      <button onClick={() => saveEdit(c)} className="text-xs text-emerald-400 hover:text-emerald-200 underline">Save</button>
                      <button onClick={() => setEditingId(null)} className="text-xs text-slate-400 underline">Cancel</button>
                    </div>
                  ) : (
                    <button onClick={() => startEdit(c)} className="text-xs text-blue-400 hover:text-blue-200 underline">Edit DQ</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

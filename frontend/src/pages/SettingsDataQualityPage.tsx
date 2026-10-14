import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { getSettings, updateSettings } from '../api/settings';
import { getDataQuality } from '../api/graph';
import type { DataQualityComponent } from '../types';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

export function SettingsDataQualityPage() {
  const { activeScenarioId } = useScenario();
  const [threshold, setThreshold] = useState(72);
  const [inputVal, setInputVal] = useState('72');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saveOk, setSaveOk] = useState(false);
  const [components, setComponents] = useState<DataQualityComponent[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getSettings().then(s => { setThreshold(s.freshness_threshold_hours); setInputVal(String(s.freshness_threshold_hours)); }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!activeScenarioId) return;
    setLoading(true);
    getDataQuality(activeScenarioId).then(dq => setComponents(dq.components)).catch(() => {}).finally(() => setLoading(false));
  }, [activeScenarioId]);

  const handleSave = async () => {
    const val = parseInt(inputVal, 10);
    if (isNaN(val) || val < 1 || val > 8760) { setSaveError('Value must be 1–8760'); return; }
    setSaveError(null);
    try {
      await updateSettings(val);
      setThreshold(val);
      setSaveOk(true); setTimeout(() => setSaveOk(false), 2000);
    } catch { setSaveError('Failed to save. Previous value retained.'); setInputVal(String(threshold)); }
  };

  const buckets = [
    { name: 'Confirmed', count: components.filter(c => c.confirmation_status === 'confirmed').length },
    { name: 'Inferred', count: components.filter(c => c.confirmation_status === 'inferred').length },
    { name: 'Unknown', count: components.filter(c => c.confirmation_status === 'unknown').length },
  ];

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold text-slate-100">Settings and Data Quality</h1>

      <section className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
        <h2 className="text-slate-100 font-semibold">Freshness Threshold</h2>
        <p className="text-slate-400 text-sm">Components last observed longer than this threshold are flagged as stale.</p>
        <div className="flex items-center gap-3">
          <input type="number" min={1} max={8760} value={inputVal} onChange={e => setInputVal(e.target.value)} className="w-24 bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-2" />
          <span className="text-slate-400 text-sm">hours</span>
          <button onClick={handleSave} className="bg-blue-700 hover:bg-blue-600 text-white px-4 py-2 rounded text-sm">Save</button>
          {saveOk && <span className="text-emerald-400 text-sm">Saved</span>}
        </div>
        {saveError && <p className="text-red-400 text-sm">{saveError}</p>}
      </section>

      <section className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
        <h2 className="text-slate-100 font-semibold">Confirmation Status Distribution</h2>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={buckets} margin={{ top: 0, right: 10, bottom: 0, left: 0 }}>
              <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: '1px solid #334155', color: '#f1f5f9' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="bg-slate-900 border border-slate-700 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-700">
            <tr>
              {['Name','Evidence Source','Confirmation','DQ Score','Last Observed','Stale'].map(h => (
                <th key={h} className="text-left text-slate-400 px-4 py-3 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="px-4 py-6 text-slate-500 text-center">Loading…</td></tr>
            ) : (
              components.map(c => (
                <tr key={c.component_id} className="border-b border-slate-800">
                  <td className="px-4 py-3 text-slate-200">{c.name}</td>
                  <td className="px-4 py-3 text-slate-400 capitalize text-xs">{c.evidence_source.replace(/_/g,' ')}</td>
                  <td className="px-4 py-3 text-slate-400 capitalize">{c.confirmation_status}</td>
                  <td className="px-4 py-3"><span className={(c.data_quality_score < 50 ? 'text-amber-400' : 'text-emerald-400') + ' font-mono'}>{c.data_quality_score}</span></td>
                  <td className="px-4 py-3 text-slate-500 text-xs">{c.last_observed_at ? new Date(c.last_observed_at).toLocaleDateString() : 'N/A'}</td>
                  <td className="px-4 py-3">{c.is_stale ? <span className="text-amber-400 text-xs">Stale</span> : <span className="text-emerald-400 text-xs">Fresh</span>}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>
    </div>
  );
}

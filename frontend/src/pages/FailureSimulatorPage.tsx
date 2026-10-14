import { useEffect, useState } from 'react';
import { useScenario } from '../contexts/ScenarioContext';
import { useSimulation } from '../contexts/SimulationContext';
import { getGraph } from '../api/graph';
import { runSimulation, resetSimulation } from '../api/simulations';
import { createScenario } from '../api/scenarios';
import type { Component, Edge, ImpactReport, FailureType } from '../types';
import { AlertTriangle } from 'lucide-react';

// Re-export for lazy import
import { createScenario as createS } from '../api/scenarios';

const FAILURE_TYPES_COMPONENT: FailureType[] = ['component_unavailable', 'component_degraded'];
const FAILURE_TYPES_EDGE: FailureType[] = ['dependency_link_unavailable'];

export function FailureSimulatorPage() {
  const { activeScenarioId, refreshScenarios } = useScenario();
  const { simulationOverlay, setSimulationOverlay, clearOverlay } = useSimulation();

  const [components, setComponents] = useState<Component[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [targetType, setTargetType] = useState<'component' | 'edge'>('component');
  const [targetId, setTargetId] = useState('');
  const [failureType, setFailureType] = useState<FailureType>('component_unavailable');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveNameInput, setSaveNameInput] = useState('');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!activeScenarioId) return;
    getGraph(activeScenarioId).then(g => {
      setComponents(g.components);
      setEdges(g.edges);
      if (g.components.length > 0) setTargetId(g.components[0].id);
    }).catch(() => setError('Failed to load graph'));
  }, [activeScenarioId]);

  useEffect(() => {
    if (targetType === 'component') {
      setFailureType('component_unavailable');
      if (components.length > 0) setTargetId(components[0].id);
    } else {
      setFailureType('dependency_link_unavailable');
      if (edges.length > 0) setTargetId(edges[0].id);
    }
  }, [targetType, components, edges]);

  const handleRun = async () => {
    if (!activeScenarioId || !targetId) return;
    setRunning(true); setError(null);
    try {
      const report = await runSimulation(activeScenarioId, targetId, targetType, failureType);
      setSimulationOverlay({
        simId: report.sim_id, failedTargetId: report.failed_target_id,
        failedTargetType: report.failed_target_type, failureType: report.failure_type,
        affectedComponentIds: [...report.directly_affected.map(c => c.component_id), ...report.transitively_affected.map(c => c.component_id)],
        possibleAltComponentIds: report.possible_alt_path_components.map(c => c.component_id),
        impactReport: report,
      });
    } catch { setError('Simulation failed'); } finally { setRunning(false); }
  };

  const handleReset = async () => {
    if (!activeScenarioId) return;
    await resetSimulation(activeScenarioId).catch(() => {});
    clearOverlay();
  };

  const handleSave = async () => {
    if (!saveNameInput.trim()) { setSaveError('Name is required'); return; }
    if (!activeScenarioId) return;
    setSaving(true); setSaveError(null);
    try {
      await createScenario(saveNameInput.trim());
      await refreshScenarios();
      setSaveNameInput('');
    } catch { setSaveError('Failed to save scenario'); } finally { setSaving(false); }
  };

  const report = simulationOverlay?.impactReport;
  const failures = targetType === 'component' ? FAILURE_TYPES_COMPONENT : FAILURE_TYPES_EDGE;

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 mb-1">Failure Simulator</h1>
        <p className="text-slate-400 text-sm">Simulate component or dependency failures to understand blast radius</p>
      </div>
      {error && <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-300 text-sm">{error}</div>}

      <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
        <div className="flex gap-4">
          {(['component','edge'] as const).map(t => (
            <button key={t} onClick={() => setTargetType(t)} className={(targetType === t ? 'bg-blue-700 text-white' : 'bg-slate-800 text-slate-300') + ' px-4 py-2 rounded text-sm capitalize'}>{t}</button>
          ))}
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-slate-400 text-sm block mb-1">Target {targetType}</label>
            <select value={targetId} onChange={e => setTargetId(e.target.value)} className="w-full bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-2">
              {targetType === 'component'
                ? components.map(c => <option key={c.id} value={c.id}>{c.name}</option>)
                : edges.map(e => <option key={e.id} value={e.id}>{e.label ?? e.id.slice(0,12) + '...'}</option>)
              }
            </select>
          </div>
          <div>
            <label className="text-slate-400 text-sm block mb-1">Failure type</label>
            <select value={failureType} onChange={e => setFailureType(e.target.value as FailureType)} className="w-full bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-2">
              {failures.map(f => <option key={f} value={f}>{f.replace(/_/g,' ')}</option>)}
            </select>
          </div>
        </div>
        <div className="flex gap-3">
          <button onClick={handleRun} disabled={running || !targetId} className="bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white px-5 py-2 rounded text-sm font-medium">
            {running ? 'Running…' : 'Run Simulation'}
          </button>
          {simulationOverlay && (
            <button onClick={handleReset} className="bg-slate-700 hover:bg-slate-600 text-slate-100 px-5 py-2 rounded text-sm">Reset Simulation</button>
          )}
        </div>
      </div>

      {report && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-6 space-y-4">
          <h2 className="text-slate-100 font-semibold">Impact Report</h2>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div><p className="text-3xl font-bold font-mono text-red-400">{report.impact_score}</p><p className="text-slate-400 text-xs">Impact Score</p></div>
            <div><p className="text-3xl font-bold font-mono text-amber-400">{report.directly_affected.length + report.transitively_affected.length}</p><p className="text-slate-400 text-xs">Affected Services</p></div>
            <div><p className="text-3xl font-bold font-mono text-blue-400">{report.data_confidence_score}</p><p className="text-slate-400 text-xs">Data Confidence</p></div>
          </div>
          <p className="text-slate-500 text-xs italic">{report.score_breakdown.label}</p>
          {report.low_confidence_notice && (
            <div className="flex items-start gap-2 bg-amber-900/20 border border-amber-700 rounded p-3 text-amber-300 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{report.low_confidence_notice}</span>
            </div>
          )}
          {report.directly_affected.length > 0 && (
            <div>
              <h3 className="text-slate-400 text-sm mb-2">Directly affected</h3>
              <ul className="space-y-1">
                {report.directly_affected.map(c => (
                  <li key={c.component_id} className="text-sm text-slate-200 flex items-center gap-2">
                    <span className="w-2 h-2 bg-red-500 rounded-full inline-block" aria-hidden />
                    {c.name}
                    {c.possible_alternative_sources.length > 0 && (
                      <span className="text-xs text-blue-400">(possible alt via {c.possible_alternative_sources.join(', ')})</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {report.transitively_affected.length > 0 && (
            <div>
              <h3 className="text-slate-400 text-sm mb-2">Transitively affected</h3>
              <ul className="space-y-1">
                {report.transitively_affected.map(c => (
                  <li key={c.component_id} className="text-sm text-slate-300 flex items-center gap-2">
                    <span className="w-2 h-2 bg-amber-500 rounded-full inline-block" aria-hidden />
                    {c.name}
                  </li>
                ))}
              </ul>
            </div>
          )}
          <div className="border-t border-slate-700 pt-4 space-y-2">
            <h3 className="text-slate-400 text-sm">Save as new scenario</h3>
            <div className="flex gap-2">
              <input value={saveNameInput} onChange={e => setSaveNameInput(e.target.value)} placeholder="New scenario name" className="flex-1 bg-slate-800 border border-slate-600 text-slate-100 text-sm rounded px-3 py-2" />
              <button onClick={handleSave} disabled={saving} className="bg-blue-700 hover:bg-blue-600 disabled:opacity-50 text-white px-4 py-2 rounded text-sm">
                {saving ? 'Saving…' : 'Save'}
              </button>
            </div>
            {saveError && <p className="text-red-400 text-xs">{saveError}</p>}
          </div>
        </div>
      )}
    </div>
  );
}

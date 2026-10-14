import { X, CheckCircle, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';
import type { Component } from '../../types';
import { useSimulation } from '../../contexts/SimulationContext';
import type { ReactNode } from 'react';

const STATUS_ICONS: Record<string, ReactNode> = {
  healthy: <CheckCircle className="w-4 h-4 text-emerald-400" aria-label="Healthy" />,
  degraded: <AlertTriangle className="w-4 h-4 text-amber-400" aria-label="Degraded" />,
  failed: <XCircle className="w-4 h-4 text-red-400" aria-label="Failed" />,
  unknown: <HelpCircle className="w-4 h-4 text-slate-400" aria-label="Unknown" />,
};

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <dt className="text-slate-400">{label}</dt>
      <dd className="text-slate-200 capitalize text-right max-w-[160px] truncate">{value}</dd>
    </div>
  );
}

export function DetailsPanel({ component, onClose }: { component: Component | null; onClose: () => void }) {
  const { simulationOverlay, setHighlightedPathIds } = useSimulation();
  if (!component) return null;
  const paths = simulationOverlay?.impactReport.impact_paths.filter(p => p.affected_component_id === component.id) ?? [];
  const isUnknown = component.confirmation_status === 'unknown';
  return (
    <aside className="w-80 shrink-0 bg-slate-900 border-l border-slate-700 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <h2 className="font-semibold text-slate-100 truncate">{component.name}</h2>
        <button onClick={onClose} className="text-slate-400 hover:text-slate-100 p-1 rounded" aria-label="Close details panel">
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <section>
          <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Overview</h3>
          <dl className="space-y-1.5 text-sm">
            <Row label="Type" value={component.type.replace(/_/g, ' ')} />
            <div className="flex justify-between items-center">
              <dt className="text-slate-400">Status</dt>
              <dd className="flex items-center gap-1 text-slate-200">
                {STATUS_ICONS[component.health_status]}
                <span className="capitalize">{component.health_status}</span>
              </dd>
            </div>
            <Row label="Criticality" value={component.criticality} />
            <Row label="Evidence" value={component.evidence_source.replace(/_/g, ' ')} />
            <div className="flex justify-between">
              <dt className="text-slate-400">Confirmation</dt>
              <dd className={`capitalize ${isUnknown ? 'text-amber-400' : 'text-slate-200'}`}>
                {isUnknown ? '! ' : ''}{component.confirmation_status}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-slate-400">DQ Score</dt>
              <dd className={`font-mono ${component.data_quality_score < 50 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {component.data_quality_score}/100
              </dd>
            </div>
          </dl>
        </section>
        {simulationOverlay && paths.length > 0 && (
          <section>
            <h3 className="text-xs font-semibold text-slate-500 uppercase mb-2">Impact Paths ({paths.length})</h3>
            <div className="space-y-2">
              {paths.map((path, i) => (
                <button key={i} onClick={() => setHighlightedPathIds(path.path_steps.map(s => s.component_id))} className="w-full text-left p-2 rounded bg-slate-800 hover:bg-slate-700 text-xs space-y-1">
                  <p className="text-slate-300">{path.path_steps.map(s => s.component_name).join(' -> ')}</p>
                  <p className="text-slate-400 line-clamp-2">{path.explanation_text}</p>
                  {path.has_dq_warning && <p className="text-amber-400">Low data quality on this path</p>}
                </button>
              ))}
            </div>
          </section>
        )}
      </div>
    </aside>
  );
}

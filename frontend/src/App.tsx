import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Suspense, lazy, useState } from 'react';
import { ScenarioProvider } from './contexts/ScenarioContext';
import { SimulationProvider } from './contexts/SimulationContext';
import { TopBar } from './components/layout/TopBar';
import { Sidebar } from './components/layout/Sidebar';
import { DetailsPanel } from './components/layout/DetailsPanel';
import type { Component } from './types';
import { useSimulation } from './contexts/SimulationContext';

function PlaceholderPage(name: string) {
  return function Page() {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <p className="text-2xl font-bold text-slate-300 mb-2">{name}</p>
          <p className="text-sm text-slate-500">Implementation coming soon</p>
        </div>
      </div>
    );
  };
}

const OverviewPage = lazy(() => import('./pages/OverviewPage').then(m => ({ default: m.OverviewPage })).catch(() => ({ default: PlaceholderPage('Overview') })));
const DependencyMapPage = lazy(() => import('./pages/DependencyMapPage').then(m => ({ default: m.DependencyMapPage })).catch(() => ({ default: PlaceholderPage('Dependency Map') })));
const FailureSimulatorPage = lazy(() => import('./pages/FailureSimulatorPage').then(m => ({ default: m.FailureSimulatorPage })).catch(() => ({ default: PlaceholderPage('Failure Simulator') })));
const IncidentAnalysisPage = lazy(() => import('./pages/IncidentAnalysisPage').then(m => ({ default: m.IncidentAnalysisPage })).catch(() => ({ default: PlaceholderPage('Incident Analysis') })));
const RecoveryPlannerPage = lazy(() => import('./pages/RecoveryPlannerPage').then(m => ({ default: m.RecoveryPlannerPage })).catch(() => ({ default: PlaceholderPage('Recovery Planner') })));
const InfrastructureInventoryPage = lazy(() => import('./pages/InfrastructureInventoryPage').then(m => ({ default: m.InfrastructureInventoryPage })).catch(() => ({ default: PlaceholderPage('Infrastructure Inventory') })));
const SimulationHistoryPage = lazy(() => import('./pages/SimulationHistoryPage').then(m => ({ default: m.SimulationHistoryPage })).catch(() => ({ default: PlaceholderPage('Simulation History') })));
const SettingsDataQualityPage = lazy(() => import('./pages/SettingsDataQualityPage').then(m => ({ default: m.SettingsDataQualityPage })).catch(() => ({ default: PlaceholderPage('Settings and Data Quality') })));

function AppLayout() {
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const { setSelectedComponentId } = useSimulation();
  const handleSelect = (comp: Component | null) => {
    setSelectedComponent(comp);
    setSelectedComponentId(comp?.id ?? null);
  };
  return (
    <div className="h-screen flex flex-col bg-slate-950 text-slate-100 overflow-hidden min-w-[1280px]">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-auto bg-slate-950">
          <Suspense fallback={<div className="flex items-center justify-center h-full text-slate-400">Loading</div>}>
            <Routes>
              <Route path="/" element={<OverviewPage />} />
              <Route path="/dependency-map" element={<DependencyMapPage />} />
              <Route path="/simulator" element={<FailureSimulatorPage />} />
              <Route path="/incidents" element={<IncidentAnalysisPage />} />
              <Route path="/recovery" element={<RecoveryPlannerPage />} />
              <Route path="/inventory" element={<InfrastructureInventoryPage />} />
              <Route path="/history" element={<SimulationHistoryPage />} />
              <Route path="/settings" element={<SettingsDataQualityPage />} />
            </Routes>
          </Suspense>
        </main>
        <DetailsPanel component={selectedComponent} onClose={() => handleSelect(null)} />
      </div>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <ScenarioProvider>
        <SimulationProvider>
          <AppLayout />
        </SimulationProvider>
      </ScenarioProvider>
    </BrowserRouter>
  );
}

export default App;

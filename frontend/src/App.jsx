import React, { useState } from 'react';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import FirewallRules from './pages/FirewallRules';
import DatasetTesting from './pages/DatasetTesting';
import SimulationResults from './pages/SimulationResults';
import SimulationHistory from './pages/SimulationHistory';
import PolicyAnalysis from './pages/PolicyAnalysis';
import PolicyComparison from './pages/PolicyComparison';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSimulationId, setSelectedSimulationId] = useState(null);

  const handleOpenResults = (simId) => {
    setSelectedSimulationId(simId);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 flex flex-col font-sans">
      <Navbar />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => {
            setActiveTab(tab);
          }}
        />

        <main className="flex-1 overflow-y-auto bg-[#0b0f19]">
          {activeTab === 'dashboard' && (
            <Dashboard
              onNavigateToResults={(id) => handleOpenResults(id)}
              onNavigateToRules={() => setActiveTab('rules')}
              onNavigateToTesting={() => setActiveTab('dataset')}
            />
          )}

          {activeTab === 'rules' && <FirewallRules />}

          {activeTab === 'dataset' && (
            <DatasetTesting
              onSimulationComplete={(id) => handleOpenResults(id)}
            />
          )}

          {activeTab === 'results' && (
            <SimulationResults
              simulationId={selectedSimulationId}
              onBackToHistory={() => setActiveTab('history')}
            />
          )}

          {activeTab === 'history' && (
            <SimulationHistory
              onOpenSimulation={(id) => handleOpenResults(id)}
            />
          )}

          {activeTab === 'analysis' && (
            <PolicyAnalysis
              onNavigateToRules={() => setActiveTab('rules')}
            />
          )}

          {activeTab === 'comparison' && (
            <PolicyComparison />
          )}
        </main>
      </div>
    </div>
  );
}


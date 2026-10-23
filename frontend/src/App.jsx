import React, { useState } from 'react';
import { ThemeProvider } from './context/ThemeContext';
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import FirewallRules from './pages/FirewallRules';
import DatasetTesting from './pages/DatasetTesting';
import SimulationResults from './pages/SimulationResults';
import SimulationHistory from './pages/SimulationHistory';
import PolicyAnalysis from './pages/PolicyAnalysis';
import PolicyComparison from './pages/PolicyComparison';
import AIAssistantDrawer from './components/AIAssistantDrawer';

function AppInner() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedSimulationId, setSelectedSimulationId] = useState(null);
  const [assistantOpen, setAssistantOpen] = useState(false);

  const handleOpenResults = (simId) => {
    setSelectedSimulationId(simId);
    setActiveTab('results');
  };

  return (
    <div className="min-h-screen flex flex-col font-sans bg-page text-page">
      <Navbar onOpenAssistant={() => setAssistantOpen(true)} />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeTab={activeTab}
          onSelectTab={(tab) => { setActiveTab(tab); }}
        />

        <main className="flex-1 overflow-y-auto bg-page">
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

      <AIAssistantDrawer
        open={assistantOpen}
        onClose={() => setAssistantOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AppInner />
    </ThemeProvider>
  );
}

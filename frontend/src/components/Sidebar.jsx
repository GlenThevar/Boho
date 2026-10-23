import React from 'react';
import {
  DashboardCircleIcon,
  Shield02Icon,
  Table01Icon,
  Activity01Icon,
  Clock01Icon,
  Shield01Icon,
  GitCompareIcon,
} from 'hugeicons-react';

export default function Sidebar({ activeTab, onSelectTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: DashboardCircleIcon },
    { id: 'rules', label: 'Firewall Rules', icon: Shield02Icon },
    { id: 'dataset', label: 'Dataset Testing', icon: Table01Icon },
    { id: 'results', label: 'Simulation Results', icon: Activity01Icon },
    { id: 'history', label: 'Simulation History', icon: Clock01Icon },
    { id: 'analysis', label: 'Policy Analysis', icon: Shield01Icon },
    { id: 'comparison', label: 'Policy Comparison', icon: GitCompareIcon },
  ];

  return (
    <aside className="w-64 border-r border-border flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)] bg-card">
      <div className="p-4 space-y-1">
        <div className="text-[11px] font-semibold uppercase tracking-wider px-3 py-2">
          Navigation
        </div>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                isActive
                  ? 'font-bold underline underline-offset-2'
                  : 'hover:opacity-60'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className="w-4 h-4" />
                <span>{item.label}</span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}

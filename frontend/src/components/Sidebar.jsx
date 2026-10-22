import React from 'react';
import {
  LayoutDashboard,
  ShieldAlert,
  FileSpreadsheet,
  Activity,
  History,
  ShieldCheck,
  GitCompare
} from 'lucide-react';

export default function Sidebar({ activeTab, onSelectTab }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'rules', label: 'Firewall Rules', icon: ShieldAlert },
    { id: 'dataset', label: 'Dataset Testing', icon: FileSpreadsheet },
    { id: 'results', label: 'Simulation Results', icon: Activity },
    { id: 'history', label: 'Simulation History', icon: History },
    { id: 'analysis', label: 'Policy Analysis', icon: ShieldCheck, badge: 'Stage 2' },
    { id: 'comparison', label: 'Policy Comparison', icon: GitCompare, badge: 'Stage 2' },
  ];

  return (
    <aside className="w-64 border-r border-slate-800 bg-[#0d121f] flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="p-4 space-y-1">
        <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 px-3 py-2">
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
                  ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50 border border-transparent'
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span className="text-[9px] uppercase font-bold tracking-wider px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono">
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      <div className="p-4 m-3 rounded-lg bg-slate-900/60 border border-slate-800 text-xs text-slate-400 space-y-2">
        <div className="font-semibold text-slate-300 flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
          <span>Security Audit Active</span>
        </div>
        <p className="text-[11px] leading-relaxed text-slate-400">
          Evaluates rule shadowing, redundancy, and permissions deterministically.
        </p>
      </div>
    </aside>
  );
}


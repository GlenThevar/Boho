import React from 'react';
import { Shield, Radio, Terminal } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center space-x-3">
        <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.25)]">
          <Shield className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <span className="font-bold text-lg tracking-wider text-slate-100 font-mono">BOHO</span>
            <span className="text-[10px] uppercase font-semibold tracking-wider px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60 font-mono">
              Stage 2: Policy Analysis
            </span>
          </div>
          <p className="text-xs text-slate-400">Firewall Policy Simulation, Security Audit & Testing Platform</p>
        </div>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="font-mono text-emerald-400 font-semibold">Offline Simulation Engine</span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400">Host OS Safe</span>
        </div>
        <div className="flex items-center space-x-1.5 text-xs text-slate-400 font-mono bg-slate-950/60 px-3 py-1.5 rounded-md border border-slate-800">
          <Terminal className="w-3.5 h-3.5 text-cyan-400" />
          <span>v1.0-stage1</span>
        </div>
      </div>
    </header>
  );
}

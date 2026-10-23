import React from 'react';
import {
  Cancel01Icon as X,
  Camera01Icon as Camera,
  Shield01Icon as Shield,
} from 'hugeicons-react';

export default function SnapshotModal({ isOpen, onClose, rules = [], simulationName = '' }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
      <div className="bg-[#111726] border border-slate-700 w-full max-w-4xl rounded-xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150 max-h-[85vh] flex flex-col">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-cyan-950/80 border border-cyan-500/30 text-cyan-400">
              <Camera className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-100">
                Firewall Rule Snapshot: {simulationName}
              </h3>
              <p className="text-xs text-slate-400">
                Preserved rules configuration as evaluated during this simulation.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-200 p-1.5 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto space-y-4">
          <div className="p-3 bg-slate-900/60 rounded-lg border border-slate-800 text-xs text-slate-400">
            This snapshot preserves historical integrity. Modifying or deleting active rules in the Rules page never alters this record.
          </div>

          <div className="border border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/90 text-slate-400 uppercase tracking-wider font-mono text-[11px] border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Priority</th>
                  <th className="py-2.5 px-3 font-semibold">Rule Name</th>
                  <th className="py-2.5 px-3 font-semibold">Protocol</th>
                  <th className="py-2.5 px-3 font-semibold">Source IP</th>
                  <th className="py-2.5 px-3 font-semibold">Destination IP</th>
                  <th className="py-2.5 px-3 font-semibold">Port</th>
                  <th className="py-2.5 px-3 font-semibold">Action</th>
                  <th className="py-2.5 px-3 font-semibold">Active</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono">
                {rules.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="py-6 text-center text-slate-500 font-sans">
                      No rules were present when this simulation ran. Only default DENY was applied.
                    </td>
                  </tr>
                ) : (
                  rules.map((rule, idx) => (
                    <tr key={rule.id || idx} className="hover:bg-slate-900/40">
                      <td className="py-2.5 px-3 font-bold text-cyan-400">#{rule.priority}</td>
                      <td className="py-2.5 px-3 font-sans font-medium text-slate-200">{rule.name}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rule.protocol}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rule.source_ip}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rule.destination_ip}</td>
                      <td className="py-2.5 px-3 text-slate-300">{rule.destination_port}</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          rule.action === 'ALLOW' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-red-500/20 text-red-400'
                        }`}>
                          {rule.action}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className={`text-[11px] ${rule.enabled ? 'text-emerald-400' : 'text-slate-500'}`}>
                          {rule.enabled ? 'Yes' : 'No'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="px-6 py-3 bg-slate-900/60 border-t border-slate-800 flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 rounded-lg"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
